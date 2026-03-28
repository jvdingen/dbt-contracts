"""Tests for the generate CLI command."""

from pathlib import Path

from dbt_contracts.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


class TestGenerateCommand:
    def test_generate_writes_files(self, runner, tmp_path):
        result = runner.invoke(
            cli,
            [
                "generate",
                "--contracts-dir",
                str(SAMPLE_PROJECT),
                "--models-dir",
                str(tmp_path / "models"),
                "--sources-dir",
                str(tmp_path / "sources"),
            ],
        )
        assert result.exit_code == 0
        assert "file(s) written" in result.output

    def test_generate_dry_run(self, runner):
        result = runner.invoke(
            cli,
            [
                "generate",
                "--contracts-dir",
                str(SAMPLE_PROJECT),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry run" in result.output

    def test_generate_validation_failure_aborts(self, runner, tmp_path):
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
        result = runner.invoke(cli, ["generate", "--contracts-dir", str(tmp_path)])
        assert result.exit_code == 1
        assert "Validation failed" in result.output

    def test_generate_skip_validation(self, runner, tmp_path):
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
        result = runner.invoke(
            cli,
            [
                "generate",
                "--contracts-dir",
                str(tmp_path),
                "--skip-validation",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

    def test_generate_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "generate" in result.output
