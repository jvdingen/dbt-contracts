"""Tests for dbt artifact exporters (integration-style, using real fixtures)."""

from __future__ import annotations

from pathlib import Path

import yaml

from dbt_contracts.generators.exporter import export_model_schema, export_sources
from dbt_contracts.odcs.parser import load_odcs

FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


class TestExportModelSchema:
    """export_model_schema produces valid dbt models YAML."""

    def test_with_schema(self) -> None:
        """Contract with schema exports models with columns and constraints."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        result = export_model_schema(contract)
        data = yaml.safe_load(result)

        assert data["version"] == 2
        assert len(data["models"]) == 1

        model = data["models"][0]
        assert model["name"] == "payments"
        assert model["config"]["contract"]["enforced"] is True
        assert len(model["columns"]) == 4
        assert model["columns"][0]["name"] == "payment_id"

    def test_without_schema(self) -> None:
        """Contract without schema exports empty models list."""
        contract = load_odcs(FIXTURES / "minimal_contract.odcs.yaml")
        result = export_model_schema(contract)
        data = yaml.safe_load(result)

        assert data["version"] == 2
        assert data["models"] == []

    def test_customer_summary(self) -> None:
        """Customer summary contract exports correctly."""
        contract = load_odcs(FIXTURES / "customer_summary.odcs.yaml")
        result = export_model_schema(contract)
        data = yaml.safe_load(result)

        model = data["models"][0]
        assert model["name"] == "customer_summary"
        assert len(model["columns"]) == 3
        column_names = [c["name"] for c in model["columns"]]
        assert column_names == ["customer_id", "total_payments", "last_payment_date"]


class TestExportSources:
    """export_sources produces valid dbt sources YAML with UUID name."""

    def test_source_name_is_uuid(self) -> None:
        """Source name defaults to contract UUID."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        result = export_sources(contract)
        data = yaml.safe_load(result)

        assert data["version"] == 2
        source = data["sources"][0]
        assert source["name"] == "dbb7b1eb-7628-436e-8914-2a00638ba6db"

    def test_tables_listed(self) -> None:
        """Source includes correct table names."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        result = export_sources(contract)
        data = yaml.safe_load(result)

        tables = data["sources"][0]["tables"]
        assert len(tables) == 1
        assert tables[0]["name"] == "payments"

    def test_columns_have_tests(self) -> None:
        """Source columns include data_tests for required fields."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        result = export_sources(contract)
        data = yaml.safe_load(result)

        columns = data["sources"][0]["tables"][0]["columns"]
        required_cols = [c for c in columns if "data_tests" in c]
        assert len(required_cols) == 4


