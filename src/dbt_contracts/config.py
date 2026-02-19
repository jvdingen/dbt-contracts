"""Configuration models and TOML loading for dbt-contracts."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Base model that forbids extra fields."""

    model_config = ConfigDict(extra="forbid")


class PathsConfig(StrictModel):
    """Directory paths for contract and output files."""

    odps_dir: str = "contracts/products"
    odcs_dir: str = "contracts/schemas"
    models_dir: str = "models"
    sources_dir: str = "sources"


class GenerationConfig(StrictModel):
    """Settings for dbt artifact generation."""

    dry_run: bool = False


class ValidationConfig(StrictModel):
    """Settings for contract validation."""

    default_mode: str = "lint"
    fail_on_error: bool = False


class Config(StrictModel):
    """Top-level configuration for dbt-contracts."""

    cli_mode: str = "interactive"
    paths: PathsConfig = PathsConfig()
    generation: GenerationConfig = GenerationConfig()
    validation: ValidationConfig = ValidationConfig()


@dataclass(frozen=True)
class Setting:
    """Metadata for a single config setting used by ``config set``."""

    key: str
    type: str  # "bool" or "str"
    description: str
    choices: tuple[str, ...] | None = None


SETTINGS: tuple[Setting, ...] = (
    Setting("cli_mode", "str", '"interactive" or "subcommand"', ("interactive", "subcommand")),
    Setting("paths.odps_dir", "str", "ODPS product directory"),
    Setting("paths.odcs_dir", "str", "ODCS contract directory"),
    Setting("paths.models_dir", "str", "dbt models directory"),
    Setting("paths.sources_dir", "str", "dbt sources directory"),
    Setting("generation.dry_run", "bool", "Dry run mode (true/false)"),
    Setting("validation.default_mode", "str", '"lint" or "test"', ("lint", "test")),
    Setting("validation.fail_on_error", "bool", "Fail on errors (true/false)"),
)

SETTINGS_BY_KEY: dict[str, Setting] = {s.key: s for s in SETTINGS}


def find_config_path(config_path: Path | None = None, project_root: Path | None = None) -> Path | None:
    """Discover the active config file path without loading it.

    Returns ``None`` when no config file is found.
    """
    if project_root is None:
        project_root = Path.cwd()

    if config_path is not None:
        return config_path

    standalone = project_root / "contracts" / "dbt-contracts.toml"
    if standalone.is_file():
        return standalone

    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text())
        if data.get("tool", {}).get("dbt-contracts") is not None:
            return pyproject

    return None


def load_config(config_path: Path | None = None, project_root: Path | None = None) -> Config:
    """Load configuration with resolution order.

    1. Explicit *config_path* if given
    2. ``contracts/dbt-contracts.toml`` in *project_root*
    3. ``[tool.dbt-contracts]`` in ``pyproject.toml`` in *project_root*
    4. Defaults (no config file needed)
    """
    if project_root is None:
        project_root = Path.cwd()

    resolved = find_config_path(config_path=config_path, project_root=project_root)

    if resolved is None:
        return Config()

    data = tomllib.loads(resolved.read_text())

    # pyproject.toml stores config under [tool.dbt-contracts]
    if resolved.name == "pyproject.toml":
        data = data.get("tool", {}).get("dbt-contracts", {})

    if not data:
        return Config()
    return Config(**data)
