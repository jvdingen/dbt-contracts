"""Tests for the Click CLI interface."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from dbt_contracts.cli import cli


class TestHelpFlags:
    """All commands respond to --help."""

    def test_root_help(self) -> None:
        """Root --help shows group usage."""
        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Contract-driven dbt workflow" in result.output

    def test_init_help(self) -> None:
        """Init --help shows command usage."""
        result = CliRunner().invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.output

    def test_generate_help(self) -> None:
        """Generate --help shows command usage."""
        result = CliRunner().invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate" in result.output

    def test_validate_help(self) -> None:
        """Validate --help shows command usage."""
        result = CliRunner().invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate" in result.output


class TestInit:
    """Tests for the init command."""

    def test_creates_config_and_dirs(self, tmp_path) -> None:
        """Init creates config file and expected directories."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert (Path(td) / "dbt-contracts.toml").exists()
            assert (Path(td) / "contracts" / "products").is_dir()
            assert (Path(td) / "contracts" / "schemas").is_dir()
            assert (Path(td) / "output").is_dir()

    def test_idempotent(self, tmp_path) -> None:
        """Running init twice does not fail or overwrite the config."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init"])
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "already exists" in result.output


class TestGenerate:
    """Tests for the generate command."""

    def test_missing_dir_exits_1(self, tmp_path) -> None:
        """Generate fails with exit 1 when ODPS directory is missing."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["generate"])
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_dry_run(self, tmp_path) -> None:
        """Generate --dry-run reports what it would do without writing files."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            odps_dir = Path(td) / "contracts" / "products"
            odps_dir.mkdir(parents=True)
            (odps_dir / "test.odps.yaml").write_text("apiVersion: v1\nkind: DataProduct\n")
            result = runner.invoke(cli, ["generate", "--dry-run"])
            assert result.exit_code == 0
            assert "Dry run" in result.output

    def test_calls_orchestrator(self, tmp_path) -> None:
        """Generate calls generate_for_product for each ODPS file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            odps_dir = Path(td) / "contracts" / "products"
            odps_dir.mkdir(parents=True)
            (odps_dir / "test.odps.yaml").write_text("apiVersion: v1\n")
            (Path(td) / "contracts" / "schemas").mkdir(parents=True)

            with patch("dbt_contracts.commands.generate.generate_for_product") as mock_gen:
                mock_gen.return_value = [Path(td) / "output" / "sources.yml"]
                result = runner.invoke(cli, ["generate"])
                assert result.exit_code == 0
                mock_gen.assert_called_once()


class TestValidate:
    """Tests for the validate command."""

    def test_missing_dir_exits_1(self, tmp_path) -> None:
        """Validate fails with exit 1 when ODCS directory is missing."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["validate"])
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_lint_mocked(self, tmp_path) -> None:
        """Validate calls lint_contract by default."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            odcs_dir = Path(td) / "contracts" / "schemas"
            odcs_dir.mkdir(parents=True)
            (odcs_dir / "test.odcs.yaml").write_text("id: test\n")

            with patch("dbt_contracts.commands.validate.lint_contract") as mock_lint:
                mock_lint.return_value = (True, [])
                result = runner.invoke(cli, ["validate"])
                assert result.exit_code == 0
                assert "PASSED" in result.output
                mock_lint.assert_called_once()

    def test_live_mocked(self, tmp_path) -> None:
        """Validate --live calls test_contract instead of lint_contract."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            odcs_dir = Path(td) / "contracts" / "schemas"
            odcs_dir.mkdir(parents=True)
            (odcs_dir / "test.odcs.yaml").write_text("id: test\n")

            with patch("dbt_contracts.commands.validate.test_contract") as mock_test:
                mock_test.return_value = (True, [])
                result = runner.invoke(cli, ["validate", "--live"])
                assert result.exit_code == 0
                assert "PASSED" in result.output
                mock_test.assert_called_once()


class TestSubcommandMode:
    """Behaviour when cli_mode is set to subcommand."""

    def test_bare_invocation_shows_help(self, tmp_path) -> None:
        """Running without a subcommand in subcommand mode shows help."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text('cli_mode = "subcommand"\n')
            result = runner.invoke(cli, [])
            assert result.exit_code == 0
            assert "Contract-driven dbt workflow" in result.output


class TestVerboseFlag:
    """The --verbose flag is accepted."""

    def test_verbose_accepted(self) -> None:
        """--verbose does not cause an error."""
        result = CliRunner().invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0
