"""Tests for the config command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from dbt_contracts.cli import cli


class TestConfigShow:
    """``dbt-contracts config`` prints resolved TOML."""

    def test_shows_defaults(self, tmp_path) -> None:
        """Config with no file shows default values as TOML."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config"])
            assert result.exit_code == 0
            assert 'cli_mode = "interactive"' in result.output
            assert "overwrite_existing = false" in result.output

    def test_shows_custom_values(self, tmp_path) -> None:
        """Config reflects values from dbt-contracts.toml."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text('[paths]\noutput_dir = "build"\n')
            result = runner.invoke(cli, ["config"])
            assert result.exit_code == 0
            assert 'output_dir = "build"' in result.output


class TestConfigPath:
    """``dbt-contracts config path`` shows the active config file."""

    def test_standalone_toml(self, tmp_path) -> None:
        """Reports dbt-contracts.toml when it exists."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text("")
            result = runner.invoke(cli, ["config", "path"])
            assert result.exit_code == 0
            assert "dbt-contracts.toml" in result.output

    def test_pyproject(self, tmp_path) -> None:
        """Reports pyproject.toml when it has the tool section."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "pyproject.toml").write_text('[tool.dbt-contracts]\ncli_mode = "interactive"\n')
            result = runner.invoke(cli, ["config", "path"])
            assert result.exit_code == 0
            assert "pyproject.toml" in result.output

    def test_none(self, tmp_path) -> None:
        """Reports 'none' when no config file exists."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "path"])
            assert result.exit_code == 0
            assert "No config file found" in result.output


class TestConfigSet:
    """``dbt-contracts config set`` updates dbt-contracts.toml."""

    def test_set_string_path(self, tmp_path) -> None:
        """Setting a path value updates the TOML file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "set", "paths.output_dir", "build"])
            assert result.exit_code == 0
            assert "Set" in result.output
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert 'output_dir = "build"' in content

    def test_set_boolean_true(self, tmp_path) -> None:
        """Boolean coercion works for 'true'."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "set", "generation.dry_run", "true"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert "dry_run = true" in content

    def test_set_boolean_yes(self, tmp_path) -> None:
        """Boolean coercion works for 'yes'."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "set", "generation.dry_run", "yes"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert "dry_run = true" in content

    def test_set_boolean_false(self, tmp_path) -> None:
        """Boolean coercion works for 'no'."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "set", "generation.dry_run", "no"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert "dry_run = false" in content

    def test_set_constrained_string(self, tmp_path) -> None:
        """Constrained string values are accepted when valid."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "set", "cli_mode", "subcommand"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert 'cli_mode = "subcommand"' in content

    def test_creates_toml_if_missing(self, tmp_path) -> None:
        """Creates dbt-contracts.toml when it doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            assert not (Path(td) / "dbt-contracts.toml").exists()
            result = runner.invoke(cli, ["config", "set", "cli_mode", "subcommand"])
            assert result.exit_code == 0
            assert (Path(td) / "dbt-contracts.toml").exists()

    def test_preserves_existing_values(self, tmp_path) -> None:
        """Setting one key doesn't erase other values."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text('cli_mode = "interactive"\n')
            runner.invoke(cli, ["config", "set", "paths.output_dir", "build"])
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert 'cli_mode = "interactive"' in content
            assert 'output_dir = "build"' in content


class TestConfigSetErrors:
    """Error handling for ``config set``."""

    def test_unknown_top_level_key(self, tmp_path) -> None:
        """Unknown top-level key is rejected with help text."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "foo", "bar"])
            assert result.exit_code == 1
            assert 'Unknown key "foo"' in result.output
            assert "Available keys:" in result.output

    def test_unknown_nested_key(self, tmp_path) -> None:
        """Unknown nested key is rejected with help text."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "generation.foo", "bar"])
            assert result.exit_code == 1
            assert 'Unknown key "generation.foo"' in result.output
            assert "Available keys:" in result.output

    def test_invalid_choice(self, tmp_path) -> None:
        """Invalid choice for constrained string is rejected."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "cli_mode", "banana"])
            assert result.exit_code == 1
            assert "must be one of: interactive, subcommand" in result.output

    def test_invalid_boolean(self, tmp_path) -> None:
        """Invalid boolean value is rejected."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "set", "generation.dry_run", "maybe"])
            assert result.exit_code == 1
            assert "must be true or false" in result.output


class TestConfigExport:
    """``dbt-contracts config export`` writes resolved config to a file."""

    def test_export_creates_file(self, tmp_path) -> None:
        """Export writes the resolved config to the given path."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(cli, ["config", "export", "my-config.toml"])
            assert result.exit_code == 0
            assert "Exported" in result.output
            content = (Path(td) / "my-config.toml").read_text()
            assert 'cli_mode = "interactive"' in content
            assert "overwrite_existing = false" in content

    def test_export_reflects_current_config(self, tmp_path) -> None:
        """Export includes values from the active config file."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text('[paths]\noutput_dir = "build"\n')
            result = runner.invoke(cli, ["config", "export", "backup.toml"])
            assert result.exit_code == 0
            content = (Path(td) / "backup.toml").read_text()
            assert 'output_dir = "build"' in content


class TestConfigImport:
    """``dbt-contracts config import`` loads config from a file."""

    def test_import_writes_to_dbt_contracts_toml(self, tmp_path) -> None:
        """Import writes the source file content to dbt-contracts.toml."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            source = Path(td) / "shared-config.toml"
            source.write_text('cli_mode = "subcommand"\n\n[generation]\ndry_run = true\n')
            result = runner.invoke(cli, ["config", "import", "shared-config.toml"])
            assert result.exit_code == 0
            assert "Imported" in result.output
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert 'cli_mode = "subcommand"' in content
            assert "dry_run = true" in content

    def test_import_validates_content(self, tmp_path) -> None:
        """Import rejects files with invalid config keys."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            source = Path(td) / "bad-config.toml"
            source.write_text('bogus_key = "oops"\n')
            result = runner.invoke(cli, ["config", "import", "bad-config.toml"])
            assert result.exit_code != 0

    def test_import_nonexistent_file(self, tmp_path) -> None:
        """Import fails when the source file doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["config", "import", "nope.toml"])
            assert result.exit_code != 0

    def test_roundtrip_export_import(self, tmp_path) -> None:
        """Exported config can be imported back without loss."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            (Path(td) / "dbt-contracts.toml").write_text('cli_mode = "subcommand"\n\n[paths]\noutput_dir = "dist"\n')
            runner.invoke(cli, ["config", "export", "backup.toml"])
            (Path(td) / "dbt-contracts.toml").unlink()
            result = runner.invoke(cli, ["config", "import", "backup.toml"])
            assert result.exit_code == 0
            content = (Path(td) / "dbt-contracts.toml").read_text()
            assert 'cli_mode = "subcommand"' in content
            assert 'output_dir = "dist"' in content


class TestConfigHelp:
    """Help flags work for config and subcommands."""

    def test_config_help(self) -> None:
        """Config --help shows group usage."""
        result = CliRunner().invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "Inspect and manage" in result.output

    def test_config_set_help(self) -> None:
        """Config set --help shows command usage."""
        result = CliRunner().invoke(cli, ["config", "set", "--help"])
        assert result.exit_code == 0
        assert "Set a configuration value" in result.output

    def test_config_export_help(self) -> None:
        """Config export --help shows command usage."""
        result = CliRunner().invoke(cli, ["config", "export", "--help"])
        assert result.exit_code == 0
        assert "Export" in result.output

    def test_config_import_help(self) -> None:
        """Config import --help shows command usage."""
        result = CliRunner().invoke(cli, ["config", "import", "--help"])
        assert result.exit_code == 0
        assert "Import" in result.output
