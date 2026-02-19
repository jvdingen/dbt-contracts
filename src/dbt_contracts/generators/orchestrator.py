"""Orchestrate dbt artifact generation from an ODPS data product."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

from dbt_contracts.generators.exporter import export_model_schema, export_sources
from dbt_contracts.generators.metadata import inject_metadata
from dbt_contracts.generators.quality import inject_quality_tests
from dbt_contracts.generators.sources import inject_source_config, inject_source_freshness
from dbt_contracts.odcs.parser import load_odcs_by_id
from dbt_contracts.odps.parser import load_odps
from dbt_contracts.odps.schema import InputPort, OutputPort

logger = logging.getLogger(__name__)


class DriftStatus(Enum):
    """Whether a generated file is new, unchanged, or changed relative to disk."""

    NEW = "new"
    UNCHANGED = "unchanged"
    CHANGED = "changed"


@dataclass(frozen=True)
class GeneratedFile:
    """A file planned for generation, with its content and drift status."""

    path: Path
    content: str
    drift_status: DriftStatus


def _compute_drift(path: Path, content: str) -> DriftStatus:
    if not path.exists():
        return DriftStatus.NEW
    if path.read_text(encoding="utf-8") == content:
        return DriftStatus.UNCHANGED
    return DriftStatus.CHANGED


def _rename_source(source_yaml: str, old_name: str, new_name: str) -> str:
    """Replace a source name in a dbt sources.yml YAML string."""
    data = yaml.safe_load(source_yaml)
    for source in data.get("sources", []):
        if source.get("name") == old_name:
            source["name"] = new_name
    return yaml.safe_dump(data, sort_keys=False)


def _merge_yaml_lists(yamls: list[str], key: str) -> str:
    """Merge multiple dbt YAML strings by concatenating a top-level list key."""
    items: list[dict] = []
    for y in yamls:
        data = yaml.safe_load(y)
        items.extend(data.get(key, []))
    return yaml.safe_dump({"version": 2, key: items}, sort_keys=False)


def _merge_sources(yamls: list[str]) -> str:
    """Merge multiple dbt sources.yml YAML strings into one document."""
    return _merge_yaml_lists(yamls, "sources")


def _merge_models(yamls: list[str]) -> str:
    """Merge multiple dbt schema.yml YAML strings into one document."""
    return _merge_yaml_lists(yamls, "models")


def _build_ref_set(odps_dir: Path) -> set[str]:
    """Collect all output port contract IDs across all products in odps_dir.

    Contracts in this set are other products' outputs and should use ``ref()``
    instead of ``source()`` in generated SQL.
    """
    ref_contracts: set[str] = set()
    for product_path in odps_dir.glob("**/*.odps.yaml"):
        try:
            product = load_odps(product_path)
        except (OSError, yaml.YAMLError):
            logger.warning("Skipping unreadable product file: %s", product_path)
            continue
        for port in product.outputPorts or []:
            ref_contracts.add(port.contractId)
    return ref_contracts


def _generate_model_sql(
    output_port: OutputPort,
    columns: list[str],
    contract_to_port: dict[str, str],
    contract_to_first_table: dict[str, str],
    ref_contracts: set[str],
) -> str:
    """Generate a model SQL select statement for an output port.

    Resolves each ``inputContract`` to either ``ref()`` (if the contract is
    another product's output) or ``source()`` (if it's a raw source).
    """
    if not output_port.inputContracts:
        col_list = ",\n    ".join(columns)
        return f"select\n    {col_list}\nfrom {{ /* TODO: specify input source */ }}\n"

    # Build FROM clause from the first inputContract
    first_ic = output_port.inputContracts[0]
    table_name = contract_to_first_table.get(first_ic.id)

    if first_ic.id in ref_contracts and table_name:
        from_clause = "{{ " + f"ref('{table_name}')" + " }}"
    elif table_name:
        port_name = contract_to_port.get(first_ic.id, first_ic.id)
        from_clause = "{{ " + f"source('{port_name}', '{table_name}')" + " }}"
    else:
        from_clause = "/* TODO: unknown input contract */"

    col_list = ",\n    ".join(columns)
    sql = f"select\n    {col_list}\nfrom {from_clause}\n"

    # Add additional inputContracts as comments
    for ic in output_port.inputContracts[1:]:
        ic_table = contract_to_first_table.get(ic.id, "?")
        if ic.id in ref_contracts:
            sql += f"-- JOIN {{{{ ref('{ic_table}') }}}}\n"
        else:
            ic_port = contract_to_port.get(ic.id, ic.id)
            sql += f"-- JOIN {{{{ source('{ic_port}', '{ic_table}') }}}}\n"

    return sql


def _process_input_ports(
    input_ports: list[InputPort],
    odcs_dir: Path,
    ref_contracts: set[str],
) -> tuple[list[str], dict[str, str]]:
    """Export and rename source YAML for each input port that is a raw source.

    Returns a tuple of (source_yamls, contract_to_first_table).
    """
    source_yamls: list[str] = []
    contract_to_first_table: dict[str, str] = {}

    for port in input_ports:
        try:
            contract = load_odcs_by_id(port.contractId, odcs_dir)
        except FileNotFoundError:
            logger.warning("Skipping input port '%s': contract '%s' not found", port.name, port.contractId)
            continue
        if contract.id is None:
            logger.warning("Skipping input port '%s': contract '%s' has no id", port.name, port.contractId)
            continue

        # Record the first table name for this contract
        if contract.schema_:
            for schema_obj in contract.schema_:
                name = getattr(schema_obj, "name", None)
                if name:
                    contract_to_first_table[contract.id] = name
                    break

        # Only emit source YAML for raw sources (not other products' outputs)
        if contract.id not in ref_contracts:
            raw_yaml = export_sources(contract)
            renamed = _rename_source(raw_yaml, contract.id, port.name)
            renamed = inject_source_config(renamed, contract)
            renamed = inject_source_freshness(renamed, contract)
            source_yamls.append(renamed)

    return source_yamls, contract_to_first_table


def _extract_columns(schema_obj: object) -> list[str] | None:
    """Extract column names from a schema object's properties.

    Returns a list of column names, or ``None`` if no columns are found.
    """
    properties = getattr(schema_obj, "properties", None)
    if not properties:
        return None
    columns = [col_name for prop in properties if (col_name := getattr(prop, "name", None))]
    return columns if columns else None


def _process_output_ports(
    output_ports: list[OutputPort],
    odcs_dir: Path,
    contract_to_port: dict[str, str],
    contract_to_first_table: dict[str, str],
    ref_contracts: set[str],
    product_tags: list[str] | None = None,
    product_domain: str | None = None,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Export model YAML and generate model SQL for each output port.

    Returns a tuple of (model_yamls, model_sqls) where model_sqls is a list
    of (table_name, sql) tuples.
    """
    model_yamls: list[str] = []
    model_sqls: list[tuple[str, str]] = []

    for port in output_ports:
        try:
            contract = load_odcs_by_id(port.contractId, odcs_dir)
        except FileNotFoundError:
            logger.warning("Skipping output port '%s': contract '%s' not found", port.name, port.contractId)
            continue

        model_yaml = export_model_schema(contract)
        model_yaml = inject_quality_tests(model_yaml, contract)
        model_yaml = inject_metadata(model_yaml, contract, product_tags, product_domain)
        model_yamls.append(model_yaml)

        if not contract.schema_:
            continue

        for schema_obj in contract.schema_:
            name = getattr(schema_obj, "name", None)
            if name is None:
                logger.warning("Skipping unnamed schema object in contract '%s'", contract.id or "<unknown>")
                continue

            columns = _extract_columns(schema_obj)
            if columns is None:
                logger.warning("Skipping table '%s': no columns found", name)
                continue

            sql = _generate_model_sql(
                port,
                columns,
                contract_to_port,
                contract_to_first_table,
                ref_contracts,
            )
            model_sqls.append((name, sql))

    return model_yamls, model_sqls


def plan_for_product(
    product_path: Path,
    odcs_dir: Path,
    models_dir: Path,
    sources_dir: Path,
    odps_dir: Path | None = None,
) -> list[GeneratedFile]:
    """Plan dbt artifact generation from an ODPS data-product definition.

    Returns ``GeneratedFile`` objects with drift status computed against
    existing files on disk.
    """
    product = load_odps(product_path)
    input_ports = product.inputPorts or []
    output_ports = product.outputPorts or []

    if not input_ports and not output_ports:
        return []

    # Build the set of contracts that are outputs of any product
    ref_contracts = _build_ref_set(odps_dir) if odps_dir else set()

    contract_to_port: dict[str, str] = {port.contractId: port.name for port in input_ports}

    source_yamls, contract_to_first_table = _process_input_ports(input_ports, odcs_dir, ref_contracts)
    model_yamls, model_sqls = _process_output_ports(
        output_ports,
        odcs_dir,
        contract_to_port,
        contract_to_first_table,
        ref_contracts,
        product_tags=product.tags,
        product_domain=product.domain,
    )

    # --- Build GeneratedFile list with drift status ---
    files: list[GeneratedFile] = []

    if source_yamls:
        merged = _merge_sources(source_yamls)
        sources_path = sources_dir / "sources.yml"
        files.append(GeneratedFile(sources_path, merged, _compute_drift(sources_path, merged)))

    if model_yamls:
        merged = _merge_models(model_yamls)
        schema_path = models_dir / "schema.yml"
        files.append(GeneratedFile(schema_path, merged, _compute_drift(schema_path, merged)))

    for table_name, sql in model_sqls:
        sql_path = models_dir / f"{table_name}.sql"
        files.append(GeneratedFile(sql_path, sql, _compute_drift(sql_path, sql)))

    return files


def write_files(files: list[GeneratedFile]) -> list[Path]:
    """Write generated files to disk.

    Returns list of paths written.
    """
    written: list[Path] = []
    for f in files:
        f.path.parent.mkdir(parents=True, exist_ok=True)
        f.path.write_text(f.content, encoding="utf-8")
        written.append(f.path)
    return written
