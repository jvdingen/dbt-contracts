"""Tests for the diff, sync, and import CLI commands."""

from pathlib import Path

from dbt_contracts.cli import cli

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"

SOURCE_YAML = """\
version: 2
sources:
  - name: raw_orders
    database: RAW
    schema: PUBLIC
    tables:
      - name: orders
        columns:
          - name: order_id
            data_type: NUMBER
"""


class TestDiffCommand:
    def test_diff_exits_one_when_drift(self, runner, tmp_path):
        result = runner.invoke(
            cli,
            ["diff", "--contracts-dir", str(SAMPLE_PROJECT)],
        )
        assert result.exit_code == 1
        assert "new" in result.output

    def test_diff_json_format(self, runner):
        result = runner.invoke(
            cli,
            [
                "diff",
                "--contracts-dir",
                str(SAMPLE_PROJECT),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 1
        assert '"status"' in result.output

    def test_diff_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "diff" in result.output


class TestSyncCommand:
    def test_sync_with_yes_writes_files(self, runner, tmp_path):
        result = runner.invoke(
            cli,
            [
                "sync",
                "--contracts-dir",
                str(SAMPLE_PROJECT),
                "--models-dir",
                str(tmp_path / "models"),
                "--sources-dir",
                str(tmp_path / "sources"),
                "--yes",
            ],
        )
        assert result.exit_code == 0
        assert "file(s) written" in result.output

    def test_sync_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "sync" in result.output


class TestImportCommand:
    def test_import_generates_contracts(self, runner, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        out = tmp_path / "contracts"
        result = runner.invoke(
            cli,
            ["import", str(schema), "--output-dir", str(out)],
        )
        assert result.exit_code == 0
        assert "contract(s) generated" in result.output

    def test_import_dry_run(self, runner, tmp_path):
        schema = tmp_path / "sources.yml"
        schema.write_text(SOURCE_YAML)
        result = runner.invoke(
            cli,
            ["import", str(schema), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry run" in result.output

    def test_import_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "import" in result.output
