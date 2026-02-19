"""Map ODCS server and SLA properties to dbt source configuration (database/schema, freshness)."""

from __future__ import annotations

import logging

import yaml
from open_data_contract_standard.model import OpenDataContractStandard, Server, ServiceLevelAgreementProperty

logger = logging.getLogger(__name__)

# ODCS uses plural unit names; dbt expects singular.
_UNIT_MAP: dict[str, str] = {
    "hours": "hour",
    "minutes": "minute",
    "days": "day",
    "weeks": "week",
    "hour": "hour",
    "minute": "minute",
    "day": "day",
    "week": "week",
}


def _select_server(servers: list[Server], preferred_env: str = "prod") -> Server | None:
    """Pick the best server entry, preferring *preferred_env*."""
    if not servers:
        return None
    for server in servers:
        if server.environment == preferred_env:
            return server
    return servers[0]


def _extract_db_schema(server: Server) -> tuple[str | None, str | None]:
    """Extract database and schema from a server entry.

    BigQuery uses ``project`` / ``dataset``; other warehouses use
    ``database`` / ``schema_`` (aliased as ``schema`` in ODCS).
    """
    database = server.project or server.database
    schema = server.dataset or server.schema_
    return database, schema


def inject_source_config(source_yaml: str, contract: OpenDataContractStandard) -> str:
    """Inject ``database`` and ``schema`` into a dbt sources YAML from ODCS server info."""
    servers: list[Server] = contract.servers or []
    server = _select_server(servers)
    if server is None:
        return source_yaml

    database, schema = _extract_db_schema(server)
    if not database and not schema:
        return source_yaml

    data = yaml.safe_load(source_yaml)
    if not data or "sources" not in data:
        return source_yaml

    for source in data["sources"]:
        if database:
            source["database"] = database
        if schema:
            source["schema"] = schema

    return yaml.safe_dump(data, sort_keys=False)


def _build_freshness(
    sla_properties: list[ServiceLevelAgreementProperty],
) -> dict[str, dict[str, int | str]] | None:
    """Build a dbt ``freshness`` dict from ODCS SLA properties.

    Looks for ``property == "frequency"`` (→ ``warn_after``) and
    ``property == "latency"`` (→ ``error_after``).
    """
    freshness: dict[str, dict[str, int | str]] = {}

    for sla in sla_properties:
        prop_name = (sla.property or "").lower()
        if prop_name not in ("frequency", "latency"):
            continue

        value = sla.value
        if value is None:
            continue
        try:
            count = int(value)
        except (TypeError, ValueError):
            logger.warning("Skipping SLA property '%s' with non-integer value: %s", sla.property, value)
            continue

        unit = _UNIT_MAP.get(str(sla.unit or ""), str(sla.unit or ""))

        entry = {"count": count, "period": unit}
        if prop_name == "frequency":
            freshness["warn_after"] = entry
        elif prop_name == "latency":
            freshness["error_after"] = entry

    return freshness or None


def inject_source_freshness(source_yaml: str, contract: OpenDataContractStandard) -> str:
    """Inject ``freshness`` and ``loaded_at_field`` into a dbt sources YAML from ODCS SLA properties."""
    sla_properties: list[ServiceLevelAgreementProperty] = contract.slaProperties or []
    freshness = _build_freshness(sla_properties)
    if freshness is None:
        return source_yaml

    loaded_at_field = contract.slaDefaultElement or "_loaded_at"

    data = yaml.safe_load(source_yaml)
    if not data or "sources" not in data:
        return source_yaml

    for source in data["sources"]:
        source["freshness"] = freshness
        source["loaded_at_field"] = loaded_at_field

    return yaml.safe_dump(data, sort_keys=False)
