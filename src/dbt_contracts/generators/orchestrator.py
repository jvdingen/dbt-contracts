"""Orchestrate dbt artifact generation from an ODPS data product."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dbt_contracts.generators.exporter import export_model_schema, export_sources, export_staging_sql
from dbt_contracts.generators.postprocess import merge_models, merge_sources, rename_source, rewrite_source_refs
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
    if path.read_text() == content:
        return DriftStatus.UNCHANGED
    return DriftStatus.CHANGED


def _process_input_ports(input_ports: list[InputPort], odcs_dir: Path) -> list[str]:
    """Export and rename source YAML for each input port. Returns list of YAML strings."""
    source_yamls: list[str] = []
    for port in input_ports:
        try:
            contract = load_odcs_by_id(port.contractId, odcs_dir)
        except FileNotFoundError:
            logger.warning("Skipping input port '%s': contract '%s' not found", port.name, port.contractId)
            continue
        if contract.id is None:
            logger.warning("Skipping input port '%s': contract '%s' has no id", port.name, port.contractId)
            continue
        raw_yaml = export_sources(contract)
        renamed = rename_source(raw_yaml, contract.id, port.name)
        source_yamls.append(renamed)
    return source_yamls


def _rewrite_sql_source_refs(
    sql: str,
    port: OutputPort,
    contract_id: str | None,
    contract_to_port: dict[str, str],
    fallback_port_name: str | None,
) -> str:
    """Rewrite source references in staging SQL based on lineage."""
    if contract_id is None:
        return sql

    if port.inputContracts:
        for ic in port.inputContracts:
            input_port_name = contract_to_port.get(ic.id)
            if input_port_name:
                sql = rewrite_source_refs(sql, contract_id, input_port_name)
    elif fallback_port_name:
        sql = rewrite_source_refs(sql, contract_id, fallback_port_name)

    return sql


def _process_output_ports(
    output_ports: list[OutputPort],
    odcs_dir: Path,
    contract_to_port: dict[str, str],
    fallback_port_name: str | None,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Export model YAML and staging SQL for each output port.

    Returns a tuple of (model_yamls, staging_sqls).
    """
    model_yamls: list[str] = []
    staging_sqls: list[tuple[str, str]] = []

    for port in output_ports:
        try:
            contract = load_odcs_by_id(port.contractId, odcs_dir)
        except FileNotFoundError:
            logger.warning("Skipping output port '%s': contract '%s' not found", port.name, port.contractId)
            continue

        model_yamls.append(export_model_schema(contract))

        if not contract.schema_:
            continue

        try:
            sql = export_staging_sql(contract)
        except RuntimeError:
            logger.warning("Skipping staging SQL for port '%s': export failed", port.name)
            continue

        sql = _rewrite_sql_source_refs(sql, port, contract.id, contract_to_port, fallback_port_name)

        for schema_obj in contract.schema_:
            name = getattr(schema_obj, "name", None)
            if name is None:
                logger.warning("Skipping unnamed schema object in contract '%s'", contract.id or "<unknown>")
                continue
            staging_sqls.append((name, sql))

    return model_yamls, staging_sqls


def plan_for_product(product_path: Path, odcs_dir: Path, models_dir: Path, sources_dir: Path) -> list[GeneratedFile]:
    """Plan dbt artifact generation from an ODPS data-product definition.

    Returns ``GeneratedFile`` objects with drift status computed against
    existing files on disk.
    """
    product = load_odps(product_path)
    input_ports = product.inputPorts or []
    output_ports = product.outputPorts or []

    if not input_ports and not output_ports:
        return []

    contract_to_port: dict[str, str] = {port.contractId: port.name for port in input_ports}
    fallback_port_name = input_ports[0].name if input_ports else None

    source_yamls = _process_input_ports(input_ports, odcs_dir)
    model_yamls, staging_sqls = _process_output_ports(
        output_ports, odcs_dir, contract_to_port, fallback_port_name,
    )

    # --- Build GeneratedFile list with drift status ---
    files: list[GeneratedFile] = []

    if source_yamls:
        merged = merge_sources(source_yamls)
        sources_path = sources_dir / "sources.yml"
        files.append(GeneratedFile(sources_path, merged, _compute_drift(sources_path, merged)))

    if model_yamls:
        merged = merge_models(model_yamls)
        schema_path = models_dir / "schema.yml"
        files.append(GeneratedFile(schema_path, merged, _compute_drift(schema_path, merged)))

    for table_name, sql in staging_sqls:
        sql_path = models_dir / "staging" / f"stg_{table_name}.sql"
        files.append(GeneratedFile(sql_path, sql, _compute_drift(sql_path, sql)))

    return files


def write_files(files: list[GeneratedFile]) -> list[Path]:
    """Write generated files to disk.

    Returns list of paths written.
    """
    written: list[Path] = []
    for f in files:
        f.path.parent.mkdir(parents=True, exist_ok=True)
        f.path.write_text(f.content)
        written.append(f.path)
    return written
