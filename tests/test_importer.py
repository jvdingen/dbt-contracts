"""Tests for the import module."""

import yaml

from dbt_contracts.core.importer import ImportResult, import_dbt

SOURCE_YAML = """\
version: 2
sources:
  - name: raw_orders
    database: RAW
    schema: PUBLIC
    tables:
      - name: orders
        description: Raw order data
        columns:
          - name: order_id
            data_type: NUMBER
            data_tests:
              - not_null
              - unique
          - name: amount
            data_type: NUMBER
"""

MODEL_YAML = """\
version: 2
models:
  - name: stg_orders
    description: Staged orders
    columns:
      - name: order_id
        data_type: NUMBER
        constraints:
          - type: not_null
          - type: unique
      - name: amount
        data_type: NUMBER
"""


class TestImportSources:
    def test_returns_import_result(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        assert isinstance(result, ImportResult)

    def test_generates_contract_from_source(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        assert len(result.contracts) == 1
        contract = yaml.safe_load(result.contracts[0].content)
        assert contract["kind"] == "DataContract"
        assert contract["id"] == "raw_orders"

    def test_source_preserves_database_schema(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        contract = yaml.safe_load(result.contracts[0].content)
        server = contract["servers"][0]
        assert server["database"] == "RAW"
        assert server["schema"] == "PUBLIC"

    def test_source_columns_with_tests(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        contract = yaml.safe_load(result.contracts[0].content)
        props = contract["schema"][0]["properties"]
        order_id = next(p for p in props if p["name"] == "order_id")
        assert order_id["required"] is True
        assert order_id["unique"] is True


class TestImportModels:
    def test_generates_contract_from_model(self, tmp_path):
        schema = tmp_path / "models.yml"
        schema.write_text(MODEL_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        assert len(result.contracts) == 1
        contract = yaml.safe_load(result.contracts[0].content)
        assert contract["id"] == "stg_orders"

    def test_model_columns_with_constraints(self, tmp_path):
        schema = tmp_path / "models.yml"
        schema.write_text(MODEL_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        contract = yaml.safe_load(result.contracts[0].content)
        props = contract["schema"][0]["properties"]
        order_id = next(p for p in props if p["name"] == "order_id")
        assert order_id["required"] is True
        assert order_id["unique"] is True


class TestImportDryRun:
    def test_dry_run_does_not_write(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        out = tmp_path / "out"
        result = import_dbt([schema], output_dir=out, dry_run=True)
        assert len(result.contracts) > 0
        assert not out.exists()

    def test_writes_files_when_not_dry_run(self, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = import_dbt([schema], output_dir=tmp_path / "out")
        for c in result.contracts:
            assert c.path.exists()
