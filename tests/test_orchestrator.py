"""Tests for the dbt generation orchestrator (integration tests with tmp_path)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from dbt_contracts.generators.orchestrator import generate_for_product

ODPS_FIXTURES = Path(__file__).parent / "fixtures" / "odps"
ODCS_FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


class TestGenerationProduct:
    """generation_product has 1 input + 1 output with inputContracts lineage."""

    def test_writes_expected_files(self, tmp_path: Path) -> None:
        """Generates sources.yml, schema.yml, and staging SQL."""
        files = generate_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        names = [f.name for f in files]
        assert "sources.yml" in names
        assert "schema.yml" in names
        assert "stg_customer_summary.sql" in names

    def test_sources_yml_uses_port_name(self, tmp_path: Path) -> None:
        """Source name is the input port name, not the contract UUID."""
        generate_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        sources = yaml.safe_load((tmp_path / "sources.yml").read_text())
        source_names = [s["name"] for s in sources["sources"]]
        assert "payments" in source_names
        # UUID should NOT be used as source name
        assert "dbb7b1eb-7628-436e-8914-2a00638ba6db" not in source_names

    def test_schema_yml_has_model(self, tmp_path: Path) -> None:
        """schema.yml contains the customer_summary model."""
        generate_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        schema = yaml.safe_load((tmp_path / "models" / "schema.yml").read_text())
        model_names = [m["name"] for m in schema["models"]]
        assert "customer_summary" in model_names

    def test_staging_sql_uses_input_port_source(self, tmp_path: Path) -> None:
        """Staging SQL source ref uses input port name via inputContracts lineage."""
        generate_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        sql = (tmp_path / "models" / "staging" / "stg_customer_summary.sql").read_text()
        assert "source('payments'" in sql
        # The output contract UUID should NOT appear in source refs
        assert "a1234567-b890-cdef-1234-567890abcdef" not in sql


class TestSimpleProduct:
    """simple_product has 1 input + 1 output, but output contract has no schema."""

    def test_sources_only(self, tmp_path: Path) -> None:
        """Only sources.yml is generated when output contract has no schema."""
        files = generate_for_product(
            ODPS_FIXTURES / "simple_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        names = [f.name for f in files]
        assert "sources.yml" in names
        # schema.yml should still be written (with empty models from no-schema contract)
        # but no staging SQL should be generated
        assert "stg_" not in " ".join(names)


class TestMinimalProduct:
    """minimal_product has no ports — nothing written."""

    def test_no_output(self, tmp_path: Path) -> None:
        """No files generated for a product with no ports."""
        files = generate_for_product(
            ODPS_FIXTURES / "minimal_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        assert files == []


class TestMissingContract:
    """Missing contracts are skipped with a warning."""

    def test_missing_input_contract_logs_warning(self, tmp_path: Path, caplog: object) -> None:
        """Missing input contract logs warning and skips port."""
        product_yaml = tmp_path / "product.odps.yaml"
        product_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Bad Product\n"
            "id: bad-id\n"
            "inputPorts:\n"
            "  - name: missing\n"
            "    version: 1.0.0\n"
            "    contractId: does-not-exist\n"
        )

        with caplog.at_level(logging.WARNING):  # type: ignore[union-attr]
            files = generate_for_product(product_yaml, ODCS_FIXTURES, tmp_path / "out")

        # Should not crash — missing contracts are skipped
        assert isinstance(files, list)
        assert any("does-not-exist" in r.message for r in caplog.records)  # type: ignore[union-attr]

    def test_missing_output_contract_skipped(self, tmp_path: Path) -> None:
        """Missing output contract is skipped gracefully."""
        product_yaml = tmp_path / "product.odps.yaml"
        product_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Bad Output Product\n"
            "id: bad-out-id\n"
            "outputPorts:\n"
            "  - name: missing_output\n"
            "    version: 1.0.0\n"
            "    contractId: does-not-exist-either\n"
        )

        files = generate_for_product(product_yaml, ODCS_FIXTURES, tmp_path / "out")
        assert isinstance(files, list)


class TestInputContractsLineage:
    """Output ports with inputContracts use correct input port source name."""

    def test_with_input_contracts(self, tmp_path: Path) -> None:
        """InputContracts on output port maps to correct input source name."""
        files = generate_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            tmp_path,
        )

        sql_files = [f for f in files if f.suffix == ".sql"]
        assert len(sql_files) == 1
        sql = sql_files[0].read_text()
        # Source ref should use input port name "payments" (mapped via inputContracts)
        assert "source('payments'" in sql

    def test_fallback_to_first_input_port(self, tmp_path: Path) -> None:
        """Output port without inputContracts falls back to first input port."""
        product_yaml = tmp_path / "product.odps.yaml"
        product_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: No Lineage Product\n"
            "id: no-lineage-id\n"
            "inputPorts:\n"
            "  - name: default_input\n"
            "    version: 1.0.0\n"
            "    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
            "outputPorts:\n"
            "  - name: output_no_lineage\n"
            "    version: 1.0.0\n"
            "    contractId: a1234567-b890-cdef-1234-567890abcdef\n"
        )

        files = generate_for_product(product_yaml, ODCS_FIXTURES, tmp_path / "out")
        sql_files = [f for f in files if f.suffix == ".sql"]
        assert len(sql_files) == 1
        sql = sql_files[0].read_text()
        # Should fall back to first input port name
        assert "source('default_input'" in sql
