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
        """Init creates config file, dbt project files, and expected directories."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["init", "--adapter", "duckdb"])
            assert result.exit_code == 0
            root = Path(td)
            assert (root / "dbt-contracts.toml").exists()
            assert (root / "dbt_project.yml").exists()
            assert (root / "profiles.yml").exists()
            assert (root / "contracts" / "products").is_dir()
            assert (root / "contracts" / "schemas").is_dir()
            assert (root / "models").is_dir()
            assert (root / "models" / "staging").is_dir()
            assert (root / "sources").is_dir()
            assert (root / "macros").is_dir()
            assert (root / "seeds").is_dir()
            assert (root / "tests").is_dir()
            assert (root / "analyses").is_dir()
            assert (root / "snapshots").is_dir()

    def test_dbt_project_yml_content(self, tmp_path) -> None:
        """dbt_project.yml contains the sanitized project name."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["init", "--adapter", "duckdb"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt_project.yml").read_text()
            assert "model-paths:" in content
            assert "profile:" in content

    def test_profiles_yml_uses_adapter(self, tmp_path) -> None:
        """profiles.yml contains the selected adapter type."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["init", "--adapter", "postgres"])
            assert result.exit_code == 0
            content = (Path(td) / "profiles.yml").read_text()
            assert "type: postgres" in content

    def test_idempotent(self, tmp_path) -> None:
        """Running init twice does not fail or overwrite the config."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "--adapter", "duckdb"])
            result = runner.invoke(cli, ["init", "--adapter", "duckdb"])
            assert result.exit_code == 0
            assert "already exists" in result.output.lower()


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
            (odps_dir / "test.odps.yaml").write_text("apiVersion: v1.0.0\nkind: DataProduct\nname: Test\nid: test-id\n")
            result = runner.invoke(cli, ["generate", "--dry-run"])
            # Product with no ports has no output, so exit code is 1
            assert "No output" in result.output

    def test_calls_orchestrator(self, tmp_path) -> None:
        """Generate calls plan_for_product for each ODPS file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            odps_dir = Path(td) / "contracts" / "products"
            odps_dir.mkdir(parents=True)
            (odps_dir / "test.odps.yaml").write_text("apiVersion: v1\n")
            (Path(td) / "contracts" / "schemas").mkdir(parents=True)

            with patch("dbt_contracts.commands.generate.plan_for_product") as mock_plan:
                mock_plan.return_value = []
                result = runner.invoke(cli, ["generate"])
                assert result.exit_code == 1  # no files generated
                mock_plan.assert_called_once()

    def test_yolo_mode_flag(self) -> None:
        """Generate --yolo-mode flag is accepted."""
        result = CliRunner().invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--yolo-mode" in result.output


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
