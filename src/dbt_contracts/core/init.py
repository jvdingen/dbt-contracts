"""Initialize a contracts directory for dbt-contracts."""

from __future__ import annotations

from pathlib import Path

import pydantic as pyd


class InitResult(pyd.BaseModel):
    """Result of running init."""

    contracts_dir: Path
    created: bool = True
    config_path: Path | None = None


def init(
    target_dir: Path,
    force: bool = False,
) -> InitResult:
    """Create a contracts/ directory structure with default configuration.

    Args:
        target_dir: Parent directory where contracts/ will be created.
        force: Overwrite existing contracts/ directory.

    Returns:
        InitResult describing what was created.
    """
    contracts_dir = target_dir / "contracts"

    if contracts_dir.exists() and not force:
        return InitResult(contracts_dir=contracts_dir, created=False)

    config_path = contracts_dir / "config.yaml"

    # Create directory structure
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "contracts").mkdir(exist_ok=True)
    (contracts_dir / "products").mkdir(exist_ok=True)

    # Write config template
    dbt_project_dir = _detect_dbt_project_dir(target_dir)
    config_path.write_text(_config_template(dbt_project_dir), encoding="utf-8")

    return InitResult(
        contracts_dir=contracts_dir,
        created=True,
        config_path=config_path,
    )


def _detect_dbt_project_dir(target_dir: Path) -> str:
    """Return relative path from contracts/ to the dbt project root."""
    return ".."


def _config_template(dbt_project_dir: str) -> str:
    """Generate a commented config.yaml template."""
    return f"""\
# dbt-contracts configuration
# See: https://dbt-contracts.dev/configuration/

# Path to the dbt project root (relative to this file)
dbt_project_dir: "{dbt_project_dir}"

# Default server type for generation
# default_server_type: snowflake

# Generation settings
# generation:
#   models_dir: models/generated
#   sources_dir: models/staging
#   generate_sources: true
#   generate_tests: true

# Validation settings
# validation:
#   cross_reference: true
#   min_status: draft
"""
