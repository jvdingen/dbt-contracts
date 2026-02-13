"""Orchestrate dbt artifact generation from an ODPS data product."""

from __future__ import annotations

import logging
from pathlib import Path

from dbt_contracts.generators.exporter import export_model_schema, export_sources, export_staging_sql
from dbt_contracts.generators.postprocess import merge_models, merge_sources, rename_source, rewrite_source_refs
from dbt_contracts.odcs.parser import load_odcs_by_id
from dbt_contracts.odps.parser import get_input_ports, get_output_ports, load_odps

logger = logging.getLogger(__name__)


def generate_for_product(product_path: Path, odcs_dir: Path, output_dir: Path) -> list[Path]:
    """Generate dbt project artifacts from an ODPS data-product definition.

    Resolves each port's ``contractId`` against *odcs_dir*, exports dbt
    sources / models / staging SQL via ``datacontract-cli``, and writes the
    post-processed results into *output_dir*.

    Returns:
        List of files written.
    """
    product = load_odps(product_path)
    input_ports = get_input_ports(product)
    output_ports = get_output_ports(product)

    if not input_ports and not output_ports:
        return []

    # contract_id → port name mapping (from input ports)
    contract_to_port: dict[str, str] = {port.contractId: port.name for port in input_ports}

    source_yamls: list[str] = []
    model_yamls: list[str] = []
    staging_sqls: list[tuple[str, str]] = []  # (table_name, sql)

    # --- Input ports → sources ---
    for port in input_ports:
        try:
            contract = load_odcs_by_id(port.contractId, odcs_dir)
        except FileNotFoundError:
            logger.warning("Skipping input port '%s': contract '%s' not found", port.name, port.contractId)
            continue
        # Ensure contract has an id before attempting renames
        if contract.id is None:
            logger.warning("Skipping input port '%s': contract '%s' has no id", port.name, port.contractId)
            continue
        raw_yaml = export_sources(contract)
        renamed = rename_source(raw_yaml, contract.id, port.name)
        source_yamls.append(renamed)

    # --- Output ports → models + staging SQL ---
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

        # Rewrite source refs using inputContracts lineage
        if port.inputContracts:
            for ic in port.inputContracts:
                input_port_name = contract_to_port.get(ic.id)
                if input_port_name:
                    if contract.id is not None:
                        sql = rewrite_source_refs(sql, contract.id, input_port_name)
        elif input_ports:
            # Fallback: use first input port name
            if contract.id is not None:
                sql = rewrite_source_refs(sql, contract.id, input_ports[0].name)  # TODO: improve heuristic

        for schema_obj in contract.schema_:
            # Narrow the name to a local variable so the type-checker sees it's
            # no longer Optional before appending to typed list.
            name = getattr(schema_obj, "name", None)
            if name is None:
                logger.warning("Skipping unnamed schema object in contract '%s'", contract.id or "<unknown>")
                continue
            staging_sqls.append((name, sql))

    # --- Write output files ---
    written: list[Path] = []

    if source_yamls:
        merged = merge_sources(source_yamls)
        sources_path = output_dir / "sources.yml"
        sources_path.parent.mkdir(parents=True, exist_ok=True)
        sources_path.write_text(merged)
        written.append(sources_path)

    if model_yamls:
        merged = merge_models(model_yamls)
        schema_path = output_dir / "models" / "schema.yml"
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path.write_text(merged)
        written.append(schema_path)

    for table_name, sql in staging_sqls:
        sql_path = output_dir / "models" / "staging" / f"stg_{table_name}.sql"
        sql_path.parent.mkdir(parents=True, exist_ok=True)
        sql_path.write_text(sql)
        written.append(sql_path)

    return written
