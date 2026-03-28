"""Tests for the validate CLI command."""

from pathlib import Path

from dbt_contracts.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


class TestValidateCommand:
    def test_valid_project_exits_zero(self, runner):
        result = runner.invoke(
            cli, ["validate", "--contracts-dir", str(SAMPLE_PROJECT)]
        )
        assert result.exit_code == 0
        assert "Validation passed" in result.output

    def test_shows_discovery_count(self, runner):
        result = runner.invoke(
            cli, ["validate", "--contracts-dir", str(SAMPLE_PROJECT)]
        )
        assert "2 contract(s)" in result.output
        assert "1 product(s)" in result.output

    def test_nonexistent_dir_exits_one(self, runner):
        result = runner.invoke(cli, ["validate", "--contracts-dir", "/nonexistent"])
        assert result.exit_code == 1

    def test_broken_cross_ref_exits_one(self, runner, tmp_path):
        (tmp_path / "products").mkdir()
        (tmp_path / "products" / "bad.odps.yaml").write_text(
            """
kind: DataProduct
apiVersion: v1.0.0
id: bad-product
version: 1.0.0
status: active
name: Bad Product
inputPorts:
  - name: ghost
    contractId: nonexistent
"""
        )
        result = runner.invoke(cli, ["validate", "--contracts-dir", str(tmp_path)])
        assert result.exit_code == 1
        assert "nonexistent" in result.output

    def test_validate_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "validate" in result.output
