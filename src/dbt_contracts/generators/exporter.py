"""Thin wrappers around datacontract-cli export for dbt artifact generation."""

from __future__ import annotations

from datacontract.data_contract import DataContract
from datacontract.export.exporter import ExportFormat
from open_data_contract_standard.model import OpenDataContractStandard


def export_model_schema(contract: OpenDataContractStandard) -> str:
    """Export an ODCS contract to a dbt models schema.yml YAML string.

    Returns a ``version: 2`` YAML document with one model per schema entry,
    including column definitions and constraints.
    """
    dc = DataContract(data_contract=contract)
    result = dc.export(ExportFormat.dbt)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result


def export_sources(contract: OpenDataContractStandard) -> str:
    """Export an ODCS contract to a dbt sources.yml YAML string.

    The source name defaults to the contract's ``id`` field.
    """
    dc = DataContract(data_contract=contract)
    result = dc.export(ExportFormat.dbt_sources)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result


def export_staging_sql(contract: OpenDataContractStandard) -> str:
    """Export an ODCS contract to a dbt staging SQL string.

    The generated SQL contains a ``select`` from ``{{ source(...) }}``.

    Raises:
        RuntimeError: If the contract has no schema (required for SQL generation).
    """
    if not contract.schema_:
        msg = f"Contract '{contract.id}' has no schema — cannot generate staging SQL"
        raise RuntimeError(msg)

    dc = DataContract(data_contract=contract)
    result = dc.export(ExportFormat.dbt_staging_sql)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result
