"""Configuration models and TOML loading for dbt-contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PathsConfig(BaseModel):
    """Directory paths for contract and output files."""

    model_config = ConfigDict(extra="forbid")

    odps_dir: str = "contracts/products"
    odcs_dir: str = "contracts/schemas"
    output_dir: str = "output"


class GenerationConfig(BaseModel):
    """Settings for dbt artifact generation."""

    model_config = ConfigDict(extra="forbid")

    overwrite_existing: bool = False
    dry_run: bool = False


class ValidationConfig(BaseModel):
    """Settings for contract validation."""

    model_config = ConfigDict(extra="forbid")

    default_mode: str = "lint"
    fail_on_error: bool = False


class Config(BaseModel):
    """Top-level configuration for dbt-contracts."""

    model_config = ConfigDict(extra="forbid")

    cli_mode: str = "interactive"
    paths: PathsConfig = PathsConfig()
    generation: GenerationConfig = GenerationConfig()
    validation: ValidationConfig = ValidationConfig()


def load_config(config_path: Path | None = None, project_root: Path | None = None) -> Config:
    """Load configuration with resolution order.

    1. Explicit *config_path* if given
    2. ``dbt-contracts.toml`` in *project_root*
    3. ``[tool.dbt-contracts]`` in ``pyproject.toml`` in *project_root*
    4. Defaults (no config file needed)
    """
    if project_root is None:
        project_root = Path.cwd()

    if config_path is not None:
        return _load_from_toml(config_path)

    standalone = project_root / "dbt-contracts.toml"
    if standalone.is_file():
        return _load_from_toml(standalone)

    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        tool_section = data.get("tool", {}).get("dbt-contracts")
        if tool_section is not None:
            return Config(**tool_section)

    return Config()


def _load_from_toml(path: Path) -> Config:
    """Load a Config from a standalone TOML file."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    if not data:
        return Config()
    return Config(**data)
