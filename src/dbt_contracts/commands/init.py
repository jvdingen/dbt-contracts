"""Initialize a dbt-contracts project."""

from __future__ import annotations

import re
from pathlib import Path

import questionary
import yaml
from rich.console import Console

from dbt_contracts.dbt_profiles import ADAPTERS

_DEFAULT_CONFIG = """\
# dbt-contracts configuration
# Uncomment and edit settings as needed.

# cli_mode = "interactive"  # "interactive" or "subcommand"

# [paths]
# odps_dir = "contracts/products"
# odcs_dir = "contracts/schemas"
# models_dir = "models"
# sources_dir = "sources"

# [generation]
# dry_run = false

# [validation]
# default_mode = "lint"  # "lint" or "test"
# fail_on_error = false
"""

_EXISTING_PROJECT_CONFIG = """\
# dbt-contracts configuration

[paths]
odps_dir = "contracts/products"
odcs_dir = "contracts/schemas"
models_dir = "{models_dir}"
sources_dir = "{sources_dir}"
"""

_DBT_PROJECT_TEMPLATE = """\
name: '{project_name}'
version: '1.0.0'

profile: '{project_name}'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

models:
  +persist_docs:
    relation: true
    columns: true

clean-targets:
  - "target"
  - "dbt_packages"
"""


def _sanitize_project_name(name: str) -> str:
    """Turn a directory name into a valid dbt project name (lowercase, underscores)."""
    sanitized = re.sub(r"[^a-z0-9_]", "_", name.lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "my_dbt_project"


def _read_model_paths(dbt_project_path: Path) -> str:
    """Read the first model-paths entry from dbt_project.yml, defaulting to 'models'."""
    try:
        data = yaml.safe_load(dbt_project_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            model_paths = data.get("model-paths", ["models"])
            if isinstance(model_paths, list) and model_paths:
                return str(model_paths[0])
    except (OSError, yaml.YAMLError):
        pass
    return "models"


def _print_next_steps(console: Console, adapter: str | None = None) -> None:
    """Print post-init instructions."""
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Place ODPS product files in contracts/products/")
    console.print("  2. Place ODCS contract files in contracts/schemas/")
    console.print("  3. Run [bold]dbt-contracts generate[/bold] to create dbt artifacts")
    if adapter:
        console.print(f"  4. Install dbt and the {adapter} adapter, then run [bold]dbt build[/bold]")


def run_init(project_root: Path, console: Console, adapter: str | None = None) -> None:
    """Scaffold a dbt-contracts project with a complete dbt project structure.

    Creates a default configuration file, dbt project files, and the expected
    directory structure.  Idempotent — skips existing files.

    When an existing ``dbt_project.yml`` is detected, only creates the contracts
    folder with configuration — skips dbt project scaffolding.

    If *adapter* is ``None``, prompts interactively for the database adapter.
    """
    dbt_project_path = project_root / "dbt_project.yml"
    existing_project = dbt_project_path.exists()

    if existing_project:
        _init_existing_project(project_root, dbt_project_path, console)
    else:
        _init_new_project(project_root, console, adapter)


def _init_existing_project(project_root: Path, dbt_project_path: Path, console: Console) -> None:
    """Initialize dbt-contracts in an existing dbt project."""
    console.print("[bold]Existing dbt project detected.[/bold]")
    console.print()

    # Read model-paths from dbt_project.yml
    default_models_dir = _read_model_paths(dbt_project_path)

    models_dir = questionary.text("Models directory:", default=default_models_dir).ask()
    if models_dir is None:
        return

    sources_dir = questionary.text("Sources directory:", default="sources").ask()
    if sources_dir is None:
        return

    # --- contracts/ directories ---
    for dirname in ("contracts/products", "contracts/schemas"):
        dirpath = project_root / dirname
        dirpath.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Ensured directory[/green] {dirpath}")

    # --- dbt-contracts config in contracts/ ---
    config_path = project_root / "contracts" / "dbt-contracts.toml"
    if config_path.exists():
        console.print(f"[dim]Config already exists:[/dim] {config_path}")
    else:
        config_path.write_text(
            _EXISTING_PROJECT_CONFIG.format(models_dir=models_dir, sources_dir=sources_dir),
            encoding="utf-8",
        )
        console.print(f"[green]Created[/green] {config_path}")

    _print_next_steps(console)


def _init_new_project(project_root: Path, console: Console, adapter: str | None = None) -> None:
    """Scaffold a complete new dbt project with dbt-contracts."""
    # --- Adapter selection ---
    if adapter is None:
        choices = [questionary.Choice(info.label, value=key) for key, info in ADAPTERS.items()]
        adapter = questionary.select("Which database adapter?", choices=choices).ask()
        if adapter is None:
            return

    if adapter not in ADAPTERS:
        console.print(f"[red]Unknown adapter:[/red] {adapter}")
        return

    project_name = _sanitize_project_name(project_root.name)

    # --- dbt-contracts config in contracts/ ---
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    config_path = contracts_dir / "dbt-contracts.toml"
    if config_path.exists():
        console.print(f"[dim]Config already exists:[/dim] {config_path}")
    else:
        config_path.write_text(_DEFAULT_CONFIG, encoding="utf-8")
        console.print(f"[green]Created[/green] {config_path}")

    # --- dbt_project.yml ---
    dbt_project_path = project_root / "dbt_project.yml"
    if dbt_project_path.exists():
        console.print(f"[dim]Already exists:[/dim] {dbt_project_path}")
    else:
        dbt_project_path.write_text(_DBT_PROJECT_TEMPLATE.format(project_name=project_name), encoding="utf-8")
        console.print(f"[green]Created[/green] {dbt_project_path}")

    # --- profiles.yml ---
    profiles_path = project_root / "profiles.yml"
    if profiles_path.exists():
        console.print(f"[dim]Already exists:[/dim] {profiles_path}")
    else:
        profile_content = ADAPTERS[adapter].profile.format(project_name=project_name)
        profiles_path.write_text(profile_content, encoding="utf-8")
        console.print(f"[green]Created[/green] {profiles_path}")

    # --- Directories ---
    dirs = [
        "contracts/products",
        "contracts/schemas",
        "models",
        "models/staging",
        "sources",
        "macros",
        "seeds",
        "tests",
        "analyses",
        "snapshots",
    ]
    for dirname in dirs:
        dirpath = project_root / dirname
        dirpath.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Ensured directory[/green] {dirpath}")

    _print_next_steps(console, adapter=adapter)
