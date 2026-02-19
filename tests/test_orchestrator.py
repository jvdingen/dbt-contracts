"""Tests for the dbt generation orchestrator (integration tests with tmp_path)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from dbt_contracts.generators.orchestrator import plan_for_product, write_files

ODPS_FIXTURES = Path(__file__).parent / "fixtures" / "odps"
ODCS_FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


class TestGenerationProduct:
    """generation_product has 1 input + 1 output with inputContracts lineage."""

    def test_writes_expected_files(self, tmp_path: Path) -> None:
        """Generates sources.yml, schema.yml, and model SQL."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        files = write_files(planned)

        names = [f.name for f in files]
        assert "sources.yml" in names
        assert "schema.yml" in names
        assert "customer_summary.sql" in names

    def test_sources_yml_uses_port_name(self, tmp_path: Path) -> None:
        """Source name is the input port name, not the contract UUID."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        write_files(planned)

        sources = yaml.safe_load((sources_dir / "sources.yml").read_text())
        source_names = [s["name"] for s in sources["sources"]]
        assert "payments" in source_names
        # UUID should NOT be used as source name
        assert "dbb7b1eb-7628-436e-8914-2a00638ba6db" not in source_names

    def test_schema_yml_has_model(self, tmp_path: Path) -> None:
        """schema.yml contains the customer_summary model."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        write_files(planned)

        schema = yaml.safe_load((models_dir / "schema.yml").read_text())
        model_names = [m["name"] for m in schema["models"]]
        assert "customer_summary" in model_names

    def test_model_sql_uses_input_port_source(self, tmp_path: Path) -> None:
        """Model SQL source ref uses input port name via inputContracts lineage."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        write_files(planned)

        sql = (models_dir / "customer_summary.sql").read_text()
        assert "source('payments', 'payments')" in sql
        # The output contract UUID should NOT appear in source refs
        assert "a1234567-b890-cdef-1234-567890abcdef" not in sql

    def test_model_sql_has_columns(self, tmp_path: Path) -> None:
        """Model SQL contains all columns from the output contract."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        write_files(planned)

        sql = (models_dir / "customer_summary.sql").read_text()
        assert "customer_id" in sql
        assert "total_payments" in sql
        assert "last_payment_date" in sql


class TestSimpleProduct:
    """simple_product has 1 input + 1 output, but output contract has no schema."""

    def test_sources_only(self, tmp_path: Path) -> None:
        """Only sources.yml is generated when output contract has no schema."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "simple_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        files = write_files(planned)

        names = [f.name for f in files]
        assert "sources.yml" in names
        # No model SQL should be generated
        assert not any(n.endswith(".sql") for n in names)


class TestMinimalProduct:
    """minimal_product has no ports — nothing written."""

    def test_no_output(self, tmp_path: Path) -> None:
        """No files generated for a product with no ports."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "minimal_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )

        assert planned == []


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
            planned = plan_for_product(product_yaml, ODCS_FIXTURES, tmp_path / "models", tmp_path / "sources")

        # Should not crash — missing contracts are skipped
        assert isinstance(planned, list)
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

        planned = plan_for_product(product_yaml, ODCS_FIXTURES, tmp_path / "models", tmp_path / "sources")
        assert isinstance(planned, list)


class TestInputContractsLineage:
    """Output ports with inputContracts use correct input port source name."""

    def test_with_input_contracts(self, tmp_path: Path) -> None:
        """InputContracts on output port maps to correct input source name."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        files = write_files(planned)

        sql_files = [f for f in files if f.suffix == ".sql"]
        assert len(sql_files) == 1
        sql = sql_files[0].read_text()
        # Source ref should use input port name "payments" (mapped via inputContracts)
        assert "source('payments', 'payments')" in sql


class TestRefDetection:
    """When an input contract is another product's output, use ref() instead of source()."""

    def test_ref_for_upstream_product_output(self, tmp_path: Path) -> None:
        """Input contract matching another product's output generates ref()."""
        # Create an "upstream" product whose output contract is
        # the same as our product's input contract
        upstream_yaml = tmp_path / "products" / "upstream.odps.yaml"
        upstream_yaml.parent.mkdir(parents=True, exist_ok=True)
        upstream_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Upstream Product\n"
            "id: upstream-001\n"
            "outputPorts:\n"
            "  - name: upstream_output\n"
            "    version: 1.0.0\n"
            "    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
        )

        # Create a downstream product that consumes the upstream output
        downstream_yaml = tmp_path / "products" / "downstream.odps.yaml"
        downstream_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Downstream Product\n"
            "id: downstream-001\n"
            "inputPorts:\n"
            "  - name: from_upstream\n"
            "    version: 1.0.0\n"
            "    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
            "outputPorts:\n"
            "  - name: final_output\n"
            "    version: 1.0.0\n"
            "    contractId: a1234567-b890-cdef-1234-567890abcdef\n"
            "    inputContracts:\n"
            "      - id: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
            "        version: 1.0.0\n"
        )

        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            downstream_yaml,
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=tmp_path / "products",
        )
        files = write_files(planned)

        sql_files = [f for f in files if f.suffix == ".sql"]
        assert len(sql_files) == 1
        sql = sql_files[0].read_text()
        # Should use ref() since the input is another product's output
        assert "ref('payments')" in sql
        assert "source(" not in sql

    def test_no_source_yml_for_ref_input(self, tmp_path: Path) -> None:
        """Input ports backed by another product's output don't generate source YAML."""
        upstream_yaml = tmp_path / "products" / "upstream.odps.yaml"
        upstream_yaml.parent.mkdir(parents=True, exist_ok=True)
        upstream_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Upstream Product\n"
            "id: upstream-001\n"
            "outputPorts:\n"
            "  - name: upstream_output\n"
            "    version: 1.0.0\n"
            "    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
        )

        downstream_yaml = tmp_path / "products" / "downstream.odps.yaml"
        downstream_yaml.write_text(
            "apiVersion: v1.0.0\n"
            "kind: DataProduct\n"
            "name: Downstream Product\n"
            "id: downstream-001\n"
            "inputPorts:\n"
            "  - name: from_upstream\n"
            "    version: 1.0.0\n"
            "    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
            "outputPorts:\n"
            "  - name: final_output\n"
            "    version: 1.0.0\n"
            "    contractId: a1234567-b890-cdef-1234-567890abcdef\n"
            "    inputContracts:\n"
            "      - id: dbb7b1eb-7628-436e-8914-2a00638ba6db\n"
            "        version: 1.0.0\n"
        )

        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            downstream_yaml,
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=tmp_path / "products",
        )
        files = write_files(planned)

        names = [f.name for f in files]
        # No sources.yml since the only input is a ref, not a raw source
        assert "sources.yml" not in names


class TestQualityProduct:
    """quality_product uses a contract with quality rules on the output port."""

    def test_schema_yml_has_quality_tests(self, tmp_path: Path) -> None:
        """Schema YAML includes data_tests generated from ODCS quality rules."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        planned = plan_for_product(
            ODPS_FIXTURES / "quality_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
            odps_dir=ODPS_FIXTURES,
        )
        write_files(planned)

        schema = yaml.safe_load((models_dir / "schema.yml").read_text())
        model = next(m for m in schema["models"] if m["name"] == "online_transactions")

        # Table-level: SQL rule should produce expression_is_true test
        table_tests = model.get("data_tests", [])
        assert any(
            isinstance(t, dict) and "dbt_utils.expression_is_true" in t
            for t in table_tests
        ), f"Expected expression_is_true in table data_tests, got: {table_tests}"

        # Table-level: custom dict test
        assert any(
            isinstance(t, dict) and "my_custom_test" in t
            for t in table_tests
        ), f"Expected my_custom_test in table data_tests, got: {table_tests}"

        # Table-level: custom string test
        assert "my_simple_test" in table_tests, f"Expected my_simple_test in table data_tests, got: {table_tests}"

        # Table-level: severity on warn test
        warn_test = next(
            (t for t in table_tests if isinstance(t, dict) and "my_warn_test" in t),
            None,
        )
        assert warn_test is not None, f"Expected my_warn_test in table data_tests, got: {table_tests}"
        assert warn_test["config"]["severity"] == "warn"

        # Column-level: transaction_id should have uniqueness test
        columns = model.get("columns", [])
        tid_col = next((c for c in columns if c["name"] == "transaction_id"), None)
        assert tid_col is not None
        col_tests = tid_col.get("data_tests", [])
        assert any(
            isinstance(t, dict) and "dbt_expectations.expect_column_values_to_be_unique" in t
            for t in col_tests
        ), f"Expected uniqueness test on transaction_id, got: {col_tests}"

        # Column-level: amount should have not-null test
        amt_col = next((c for c in columns if c["name"] == "amount"), None)
        assert amt_col is not None
        amt_tests = amt_col.get("data_tests", [])
        assert any(
            isinstance(t, dict) and "dbt_expectations.expect_column_values_to_not_be_null" in t
            for t in amt_tests
        ), f"Expected not-null test on amount, got: {amt_tests}"
