"""Thin wrappers around datacontract-cli export for dbt artifact generation."""

from __future__ import annotations

from datacontract.data_contract import DataContract
from datacontract.export.exporter import ExportFormat
from open_data_contract_standard.model import OpenDataContractStandard, Team, TeamMember


def _normalize_team(contract: OpenDataContractStandard) -> OpenDataContractStandard:
    """Return a shallow copy with ``team`` normalised to a ``Team`` object.

    ODCS allows ``team`` to be either a ``Team`` object or a bare
    ``list[TeamMember]``.  datacontract-cli only handles the ``Team``
    form, so we wrap the list when necessary.
    """
    if not isinstance(contract.team, list):
        return contract
    members: list[TeamMember] = contract.team
    owner = next((m for m in members if m.role == "owner"), None)
    team_name = owner.name if owner and owner.name else "team"
    return contract.model_copy(update={"team": Team(name=team_name, members=members)})


def _export(contract: OpenDataContractStandard, fmt: ExportFormat) -> str:
    """Export a contract to the given format and return a UTF-8 string."""
    safe = _normalize_team(contract)
    dc = DataContract(data_contract=safe)
    result = dc.export(fmt)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result


def export_model_schema(contract: OpenDataContractStandard) -> str:
    """Export an ODCS contract to a dbt models schema.yml YAML string.

    Returns a ``version: 2`` YAML document with one model per schema entry,
    including column definitions and constraints.
    """
    return _export(contract, ExportFormat.dbt)


def export_sources(contract: OpenDataContractStandard) -> str:
    """Export an ODCS contract to a dbt sources.yml YAML string.

    The source name defaults to the contract's ``id`` field.
    """
    return _export(contract, ExportFormat.dbt_sources)


