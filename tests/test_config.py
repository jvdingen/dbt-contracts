"""Tests for configuration loading."""

import pytest
from pydantic import ValidationError

from dbt_contracts.config import Config, GenerationConfig, PathsConfig, ValidationConfig, load_config


class TestDefaults:
    """Config models produce sensible defaults when no values are given."""

    def test_paths_defaults(self) -> None:
        """PathsConfig defaults match the expected directory layout."""
        p = PathsConfig()
        assert p.odps_dir == "contracts/products"
        assert p.odcs_dir == "contracts/schemas"
        assert p.models_dir == "models"
        assert p.sources_dir == "sources"

    def test_generation_defaults(self) -> None:
        """GenerationConfig defaults to safe settings."""
        g = GenerationConfig()
        assert g.overwrite_existing is False
        assert g.dry_run is False

    def test_validation_defaults(self) -> None:
        """ValidationConfig defaults to lint mode."""
        v = ValidationConfig()
        assert v.default_mode == "lint"
        assert v.fail_on_error is False

    def test_config_defaults(self) -> None:
        """Top-level Config uses interactive mode with nested defaults."""
        c = Config()
        assert c.cli_mode == "interactive"
        assert c.paths == PathsConfig()
        assert c.generation == GenerationConfig()
        assert c.validation == ValidationConfig()


class TestExtraFieldsForbidden:
    """Extra fields in config models are rejected."""

    def test_paths_extra(self) -> None:
        """PathsConfig rejects unknown keys."""
        with pytest.raises(ValidationError):
            PathsConfig(**{"unknown_key": "value"})

    def test_config_extra(self) -> None:
        """Top-level Config rejects unknown keys."""
        with pytest.raises(ValidationError):
            Config(**{"bogus": True})  # type: ignore[arg-type]


class TestLoadFromToml:
    """Loading config from a standalone dbt-contracts.toml file."""

    def test_standalone_toml(self, tmp_path) -> None:
        """A standalone TOML file is loaded correctly."""
        toml = tmp_path / "dbt-contracts.toml"
        toml.write_text('[paths]\nodps_dir = "my/products"\n')
        config = load_config(project_root=tmp_path)
        assert config.paths.odps_dir == "my/products"
        assert config.paths.odcs_dir == "contracts/schemas"  # default kept

    def test_empty_toml(self, tmp_path) -> None:
        """An empty TOML file falls back to defaults."""
        toml = tmp_path / "dbt-contracts.toml"
        toml.write_text("")
        config = load_config(project_root=tmp_path)
        assert config == Config()

    def test_explicit_path_override(self, tmp_path) -> None:
        """An explicit config_path takes precedence over project_root discovery."""
        explicit = tmp_path / "custom.toml"
        explicit.write_text('cli_mode = "subcommand"\n')

        # Also place a different file in project root — it should be ignored
        default = tmp_path / "dbt-contracts.toml"
        default.write_text('cli_mode = "interactive"\n')

        config = load_config(config_path=explicit, project_root=tmp_path)
        assert config.cli_mode == "subcommand"


class TestLoadFromPyproject:
    """Loading config from pyproject.toml [tool.dbt-contracts] section."""

    def test_pyproject_section(self, tmp_path) -> None:
        """Config is read from pyproject.toml when no standalone file exists."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.dbt-contracts]\ncli_mode = "subcommand"\n')
        config = load_config(project_root=tmp_path)
        assert config.cli_mode == "subcommand"

    def test_pyproject_without_section(self, tmp_path) -> None:
        """A pyproject.toml without the section falls back to defaults."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "my-project"\n')
        config = load_config(project_root=tmp_path)
        assert config == Config()


class TestPrecedence:
    """Standalone TOML takes precedence over pyproject.toml."""

    def test_standalone_wins(self, tmp_path) -> None:
        """dbt-contracts.toml is preferred over pyproject.toml."""
        (tmp_path / "dbt-contracts.toml").write_text('cli_mode = "interactive"\n')
        (tmp_path / "pyproject.toml").write_text('[tool.dbt-contracts]\ncli_mode = "subcommand"\n')
        config = load_config(project_root=tmp_path)
        assert config.cli_mode == "interactive"


class TestNoFiles:
    """When no config files exist, defaults are returned."""

    def test_no_files(self, tmp_path) -> None:
        """An empty project root produces default Config."""
        config = load_config(project_root=tmp_path)
        assert config == Config()


class TestPartialConfig:
    """Partial configs only override specified values."""

    def test_partial_nested(self, tmp_path) -> None:
        """A partial config overrides only specified nested values."""
        toml = tmp_path / "dbt-contracts.toml"
        toml.write_text("[generation]\ndry_run = true\n")
        config = load_config(project_root=tmp_path)
        assert config.generation.dry_run is True
        assert config.generation.overwrite_existing is False  # default
        assert config.cli_mode == "interactive"  # default
