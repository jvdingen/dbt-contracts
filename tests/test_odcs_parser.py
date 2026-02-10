"""Tests for ODCS YAML file loading and contract resolution."""

from pathlib import Path

import pytest

from dbt_contracts.odcs.parser import load_odcs, load_odcs_by_id

FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


class TestLoadOdcs:
    """load_odcs() from fixture path returns valid OpenDataContractStandard."""

    def test_load_simple_table(self) -> None:
        """Loading simple_table.odcs.yaml returns correct contract fields."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        assert contract.id == "dbb7b1eb-7628-436e-8914-2a00638ba6db"
        assert contract.name == "Payments Contract"
        assert contract.version == "1.0.0"
        assert contract.status == "active"

    def test_schema_and_properties(self) -> None:
        """simple_table contract has one schema with four properties."""
        contract = load_odcs(FIXTURES / "simple_table.odcs.yaml")
        assert contract.schema_ is not None
        assert len(contract.schema_) == 1
        schema = contract.schema_[0]
        assert schema.name == "payments"
        assert schema.physicalName == "raw_payments"
        assert schema.properties is not None
        assert len(schema.properties) == 4
        prop = schema.properties[0]
        assert prop.name == "payment_id"
        assert prop.primaryKey is True
        assert prop.required is True

    def test_load_minimal_contract(self) -> None:
        """Loading minimal_contract.odcs.yaml returns contract with no schema."""
        contract = load_odcs(FIXTURES / "minimal_contract.odcs.yaml")
        assert contract.id == "c2798941-1b7e-4b03-9e0d-955b1a872b32"
        assert contract.name == "Raw Transactions Contract"

    def test_load_with_quality_rules(self) -> None:
        """Loading with_quality_rules.odcs.yaml includes schema-level quality."""
        contract = load_odcs(FIXTURES / "with_quality_rules.odcs.yaml")
        assert contract.id == "ec2a112d-5cfe-49f3-8760-f9cfb4597544"
        assert contract.schema_ is not None
        schema = contract.schema_[0]
        assert schema.name == "online_transactions"
        assert schema.quality is not None
        assert len(schema.quality) == 1
        assert schema.quality[0].type == "sql"

    def test_nonexistent_file(self) -> None:
        """Loading a non-existent file raises an error."""
        with pytest.raises(Exception):  # noqa: B017
            load_odcs(FIXTURES / "nonexistent.yaml")


class TestLoadOdcsById:
    """load_odcs_by_id() resolves contracts by id from a directory."""

    def test_find_payments_contract(self) -> None:
        """Finds simple_table contract by its id."""
        contract = load_odcs_by_id("dbb7b1eb-7628-436e-8914-2a00638ba6db", FIXTURES)
        assert contract.name == "Payments Contract"

    def test_find_minimal_contract(self) -> None:
        """Finds minimal_contract by its id."""
        contract = load_odcs_by_id("c2798941-1b7e-4b03-9e0d-955b1a872b32", FIXTURES)
        assert contract.name == "Raw Transactions Contract"

    def test_find_quality_rules_contract(self) -> None:
        """Finds with_quality_rules contract by its id."""
        contract = load_odcs_by_id("ec2a112d-5cfe-49f3-8760-f9cfb4597544", FIXTURES)
        assert contract.name == "Online Transactions Contract"

    def test_unknown_id_raises(self) -> None:
        """Unknown contract id raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="No ODCS contract found"):
            load_odcs_by_id("nonexistent-id", FIXTURES)

    def test_empty_directory_raises(self, tmp_path: Path) -> None:
        """Empty directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="No ODCS contract found"):
            load_odcs_by_id("any-id", tmp_path)
