"""Tests for ODCS server → dbt source config and SLA → freshness mapping."""

from __future__ import annotations

import yaml
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.generators.sources import (
    _build_freshness,
    _extract_db_schema,
    _select_server,
    inject_source_config,
    inject_source_freshness,
)


def _make_contract(**overrides: object) -> OpenDataContractStandard:
    """Build a minimal contract, merging *overrides* into the base dict."""
    base: dict = {
        "kind": "DataContract",
        "apiVersion": "v3.1.0",
        "id": "test-src",
        "name": "Source Contract",
        "version": "1.0.0",
        "status": "active",
        "schema": [
            {
                "name": "my_table",
                "physicalType": "table",
                "properties": [
                    {"name": "col_a", "logicalType": "string"},
                ],
            },
        ],
    }
    base.update(overrides)
    return OpenDataContractStandard.model_validate(base)


def _base_source_yaml(**source_overrides: object) -> str:
    """Return a minimal dbt sources YAML string."""
    source: dict = {"name": "my_source", "tables": [{"name": "my_table"}]}
    source.update(source_overrides)
    return yaml.safe_dump({"version": 2, "sources": [source]}, sort_keys=False)


# ---------------------------------------------------------------------------
# inject_source_config
# ---------------------------------------------------------------------------


class TestSelectServer:
    """Server selection prefers prod environment."""

    def test_prefers_prod(self) -> None:
        """When a prod server exists, it is selected."""
        contract = _make_contract(
            servers=[
                {"environment": "dev", "type": "postgres", "database": "dev_db", "schema": "dev_schema"},
                {"environment": "prod", "type": "postgres", "database": "prod_db", "schema": "prod_schema"},
            ],
        )
        server = _select_server(contract.servers)
        assert server is not None
        assert server.environment == "prod"

    def test_falls_back_to_first(self) -> None:
        """Without a prod server, the first server is selected."""
        contract = _make_contract(
            servers=[
                {"environment": "staging", "type": "postgres", "database": "stage_db", "schema": "stage_schema"},
            ],
        )
        server = _select_server(contract.servers)
        assert server is not None
        assert server.environment == "staging"

    def test_no_servers(self) -> None:
        """Empty server list returns None."""
        assert _select_server([]) is None


class TestExtractDbSchema:
    """Database/schema extraction handles both standard and BigQuery servers."""

    def test_standard_server(self) -> None:
        """Standard server uses database/schema fields."""
        contract = _make_contract(
            servers=[{"type": "postgres", "database": "my_db", "schema": "my_schema"}],
        )
        db, schema = _extract_db_schema(contract.servers[0])
        assert db == "my_db"
        assert schema == "my_schema"

    def test_bigquery_server(self) -> None:
        """BigQuery server uses project/dataset fields."""
        contract = _make_contract(
            servers=[{"type": "bigquery", "project": "my-project", "dataset": "my_dataset"}],
        )
        db, schema = _extract_db_schema(contract.servers[0])
        assert db == "my-project"
        assert schema == "my_dataset"


class TestInjectSourceConfig:
    """inject_source_config adds database/schema to source entries."""

    def test_injects_database_and_schema(self) -> None:
        """Database and schema from prod server appear on source."""
        contract = _make_contract(
            servers=[
                {"environment": "prod", "type": "postgres", "database": "raw_db", "schema": "public"},
            ],
        )
        result = inject_source_config(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        source = data["sources"][0]
        assert source["database"] == "raw_db"
        assert source["schema"] == "public"

    def test_no_servers_returns_unchanged(self) -> None:
        """Contract without servers returns YAML unchanged."""
        contract = _make_contract()
        input_yaml = _base_source_yaml()
        assert inject_source_config(input_yaml, contract) == input_yaml

    def test_single_server_without_environment(self) -> None:
        """A single server without environment is still used (fallback to first)."""
        contract = _make_contract(
            servers=[{"type": "postgres", "database": "only_db", "schema": "only_schema"}],
        )
        result = inject_source_config(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        source = data["sources"][0]
        assert source["database"] == "only_db"
        assert source["schema"] == "only_schema"

    def test_bigquery_project_dataset(self) -> None:
        """BigQuery project/dataset are mapped to database/schema."""
        contract = _make_contract(
            servers=[{"type": "bigquery", "project": "gcp-project", "dataset": "raw"}],
        )
        result = inject_source_config(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        source = data["sources"][0]
        assert source["database"] == "gcp-project"
        assert source["schema"] == "raw"


# ---------------------------------------------------------------------------
# inject_source_freshness
# ---------------------------------------------------------------------------


class TestBuildFreshness:
    """Freshness dict construction from SLA properties."""

    def test_frequency_and_latency(self) -> None:
        """Both frequency and latency produce warn_after and error_after."""
        contract = _make_contract(
            slaProperties=[
                {"property": "frequency", "value": 24, "unit": "hours"},
                {"property": "latency", "value": 48, "unit": "hours"},
            ],
        )
        freshness = _build_freshness(contract.slaProperties)
        assert freshness is not None
        assert freshness["warn_after"] == {"count": 24, "period": "hour"}
        assert freshness["error_after"] == {"count": 48, "period": "hour"}

    def test_frequency_only(self) -> None:
        """Only frequency produces warn_after without error_after."""
        contract = _make_contract(
            slaProperties=[
                {"property": "frequency", "value": 12, "unit": "hours"},
            ],
        )
        freshness = _build_freshness(contract.slaProperties)
        assert freshness is not None
        assert "warn_after" in freshness
        assert "error_after" not in freshness

    def test_no_relevant_sla_returns_none(self) -> None:
        """SLA properties without frequency/latency return None."""
        contract = _make_contract(
            slaProperties=[
                {"property": "availability", "value": 99.9, "unit": "%"},
            ],
        )
        freshness = _build_freshness(contract.slaProperties)
        assert freshness is None

    def test_unit_normalization(self) -> None:
        """Plural and singular units are normalized to dbt singular form."""
        contract = _make_contract(
            slaProperties=[
                {"property": "frequency", "value": 30, "unit": "minutes"},
                {"property": "latency", "value": 2, "unit": "days"},
            ],
        )
        freshness = _build_freshness(contract.slaProperties)
        assert freshness["warn_after"]["period"] == "minute"
        assert freshness["error_after"]["period"] == "day"


class TestInjectSourceFreshness:
    """inject_source_freshness adds freshness and loaded_at_field to source entries."""

    def test_injects_freshness(self) -> None:
        """Freshness from SLA properties appears on source."""
        contract = _make_contract(
            slaProperties=[
                {"property": "frequency", "value": 24, "unit": "hours"},
                {"property": "latency", "value": 48, "unit": "hours"},
            ],
        )
        result = inject_source_freshness(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        source = data["sources"][0]
        assert source["freshness"]["warn_after"] == {"count": 24, "period": "hour"}
        assert source["freshness"]["error_after"] == {"count": 48, "period": "hour"}
        assert source["loaded_at_field"] == "_loaded_at"

    def test_no_sla_returns_unchanged(self) -> None:
        """Contract without SLA properties returns YAML unchanged."""
        contract = _make_contract()
        input_yaml = _base_source_yaml()
        assert inject_source_freshness(input_yaml, contract) == input_yaml

    def test_sla_default_element_override(self) -> None:
        """SlaDefaultElement overrides the default loaded_at_field."""
        contract = _make_contract(
            slaDefaultElement="updated_at",
            slaProperties=[
                {"property": "frequency", "value": 6, "unit": "hours"},
            ],
        )
        result = inject_source_freshness(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        source = data["sources"][0]
        assert source["loaded_at_field"] == "updated_at"

    def test_default_loaded_at_field(self) -> None:
        """Without slaDefaultElement, loaded_at_field defaults to _loaded_at."""
        contract = _make_contract(
            slaProperties=[
                {"property": "frequency", "value": 1, "unit": "day"},
            ],
        )
        result = inject_source_freshness(_base_source_yaml(), contract)
        data = yaml.safe_load(result)
        assert data["sources"][0]["loaded_at_field"] == "_loaded_at"
