"""Adapter layer wrapping datacontract-cli exporters for dbt artifact generation.

Provides lineage-aware rendering of ODCS contracts into dbt sources, models,
and staging SQL, using ODPS products to determine contract classification.
"""

from __future__ import annotations

from typing import Literal

import pydantic as pyd
import yaml
from datacontract.data_contract import DataContract
from datacontract.export.dbt_exporter import (
    DbtExporter,
    DbtSourceExporter,
)
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.models.odps import OpenDataProductStandard

ContractRole = Literal["source", "model", "ref"]


class LintResult(pyd.BaseModel):
    """Result of validating an ODCS contract against the JSON schema."""

    passed: bool
    errors: list[str] = pyd.Field(default_factory=list)


class GenerationResult(pyd.BaseModel):
    """Combined dbt artifacts produced by rendering contracts."""

    sources: list[dict] = pyd.Field(default_factory=list)
    models: list[dict] = pyd.Field(default_factory=list)
    staging_sql: dict[str, str] = pyd.Field(default_factory=dict)


def lint(contract: OpenDataContractStandard) -> LintResult:
    """Validate an ODCS contract against the JSON schema.

    Delegates to datacontract-cli's lint functionality. Serializes the contract
    to YAML first, as datacontract-cli only runs full JSON schema validation
    when receiving a YAML string (not an object).
    """
    yaml_str = contract.to_yaml()
    run = DataContract(data_contract_str=yaml_str).lint()
    errors = [
        check.reason or check.name
        for check in run.checks
        if check.result.value == "failed"
    ]
    return LintResult(passed=len(errors) == 0, errors=errors)


def render(
    contracts: list[OpenDataContractStandard],
    products: list[OpenDataProductStandard],
    default_server_type: str = "snowflake",
) -> GenerationResult:
    """Render ODCS contracts into dbt artifacts using ODPS lineage.

    Classifies each contract as source, model, or ref based on ODPS port
    definitions, then calls the appropriate datacontract-cli exporter.

    Args:
        contracts: ODCS contract objects to render.
        products: ODPS product objects defining lineage between contracts.
        default_server_type: Fallback server type when a contract has no servers.

    Returns:
        GenerationResult with sources, models, and staging SQL dicts.
    """
    contracts_by_id = {c.id: c for c in contracts if c.id}
    lineage = _build_lineage(contracts_by_id, products)
    upstream_map = _build_upstream_map(products)
    result = GenerationResult()

    for contract_id, role in lineage.items():
        contract = contracts_by_id[contract_id]
        server_name = _get_server_name(contract)
        server_type = _resolve_server_type(contract, default_server_type)

        if role == "source":
            source_dict = _export_sources(contract, server_name, server_type)
            result.sources.append(source_dict)
        else:
            model_dict = _export_model(contract, server_name, server_type)
            result.models.append(model_dict)

            upstream_ids = upstream_map.get(contract_id, [])
            for schema_obj in contract.schema_ or []:
                sql = _build_staging_sql(
                    contract,
                    schema_obj.name,
                    upstream_ids,
                    contracts_by_id,
                    lineage,
                )
                result.staging_sql[schema_obj.name] = sql

    return result


def _build_lineage(
    contracts_by_id: dict[str, OpenDataContractStandard],
    products: list[OpenDataProductStandard],
) -> dict[str, ContractRole]:
    """Classify contracts as source, model, or ref based on ODPS ports.

    Rules:
    - outputPorts.contractId -> "model"
    - inputPorts.contractId that is also an outputPort of any product -> "model"
    - inputPorts.contractId (not an output elsewhere) -> "source"
    - Contracts not in any port -> "source"
    """
    all_output_ids: set[str] = set()
    all_input_ids: set[str] = set()

    for product in products:
        for port in product.outputPorts or []:
            if port.contractId:
                all_output_ids.add(port.contractId)
        for port in product.inputPorts or []:
            if port.contractId:
                all_input_ids.add(port.contractId)

    lineage: dict[str, ContractRole] = {}

    for contract_id in contracts_by_id:
        if contract_id in all_output_ids:
            lineage[contract_id] = "model"
        elif contract_id in all_input_ids:
            lineage[contract_id] = "source"
        else:
            lineage[contract_id] = "source"

    return lineage


def _build_upstream_map(
    products: list[OpenDataProductStandard],
) -> dict[str, list[str]]:
    """Build a map of contract ID -> list of upstream contract IDs.

    Uses ODPS outputPorts.inputContracts to determine upstream dependencies.
    """
    upstream: dict[str, list[str]] = {}
    for product in products:
        for port in product.outputPorts or []:
            if port.contractId and port.inputContracts:
                upstream.setdefault(port.contractId, []).extend(port.inputContracts)
    return upstream


def _resolve_server_type(contract: OpenDataContractStandard, default: str) -> str:
    """Get the server type from a contract's first server, or fall back to default."""
    if contract.servers:
        server = contract.servers[0]
        if server.type:
            return server.type
    return default


def _get_server_name(contract: OpenDataContractStandard) -> str | None:
    """Get the server name from a contract's first server."""
    if contract.servers:
        return contract.servers[0].server
    return None


def _export_model(
    contract: OpenDataContractStandard,
    server_name: str | None,
    server_type: str,
) -> dict:
    """Export a contract as a dbt model YAML dict."""
    yaml_str = DbtExporter("dbt").export(
        data_contract=contract,
        schema_name="all",
        server=server_name,
        sql_server_type=server_type,
        export_args={},
    )
    return yaml.safe_load(yaml_str)


def _export_sources(
    contract: OpenDataContractStandard,
    server_name: str | None,
    server_type: str,
) -> dict:
    """Export a contract as a dbt sources YAML dict."""
    yaml_str = DbtSourceExporter("dbt-sources").export(
        data_contract=contract,
        schema_name="all",
        server=server_name,
        sql_server_type=server_type,
        export_args={},
    )
    return yaml.safe_load(yaml_str)


def _build_staging_sql(
    contract: OpenDataContractStandard,
    schema_name: str,
    upstream_ids: list[str],
    contracts_by_id: dict[str, OpenDataContractStandard],
    lineage: dict[str, ContractRole],
) -> str:
    """Build staging SQL for a model, referencing upstream contracts.

    If the model has upstream dependencies (from ODPS inputContracts),
    the SQL references those upstreams using source() or ref() depending
    on their lineage classification. Otherwise, falls back to the
    datacontract-cli generated SQL referencing the contract's own source.
    """
    # Get columns from the model's schema
    schema_obj = next(
        (s for s in (contract.schema_ or []) if s.name == schema_name), None
    )
    if not schema_obj or not schema_obj.properties:
        return ""

    columns = ", ".join(p.name for p in schema_obj.properties if p.name)

    if upstream_ids:
        # Reference the first upstream contract's first schema object
        upstream_id = upstream_ids[0]
        upstream = contracts_by_id.get(upstream_id)
        if upstream and upstream.schema_:
            upstream_schema = upstream.schema_[0].name
            role = lineage.get(upstream_id, "source")
            if role == "model":
                from_clause = "{{ " + f"ref('{upstream_schema}')" + " }}"
            else:
                from_clause = (
                    "{{ " + f"source('{upstream_id}', '{upstream_schema}')" + " }}"
                )
            return f"select\n    {columns}\nfrom {from_clause}\n"

    # No upstream: reference the contract's own source
    from_clause = "{{ " + f"source('{contract.id}', '{schema_name}')" + " }}"
    return f"select\n    {columns}\nfrom {from_clause}\n"
