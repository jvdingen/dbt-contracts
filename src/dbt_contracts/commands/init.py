"""Initialize a dbt-contracts project."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

_DEFAULT_CONFIG = """\
# dbt-contracts configuration
# Uncomment and edit settings as needed.

# cli_mode = "interactive"  # "interactive" or "subcommand"

# [paths]
# odps_dir = "contracts/products"
# odcs_dir = "contracts/schemas"
# output_dir = "output"

# [generation]
# overwrite_existing = false
# dry_run = false

# [validation]
# default_mode = "lint"  # "lint" or "test"
# fail_on_error = false
"""


def run_init(project_root: Path, console: Console) -> None:
    """Scaffold a dbt-contracts project in *project_root*.

    Creates a default configuration file and the expected directory structure.
    Idempotent — skips existing config and uses ``mkdir(exist_ok=True)``.
    """
    config_path = project_root / "dbt-contracts.toml"
    if config_path.exists():
        console.print(f"[dim]Config already exists:[/dim] {config_path}")
    else:
        config_path.write_text(_DEFAULT_CONFIG)
        console.print(f"[green]Created[/green] {config_path}")

    for dirname in ("contracts/products", "contracts/schemas", "output"):
        dirpath = project_root / dirname
        dirpath.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Ensured directory[/green] {dirpath}")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Place ODPS product files in contracts/products/")
    console.print("  2. Place ODCS contract files in contracts/schemas/")
    console.print("  3. Run [bold]dbt-contracts generate[/bold] to create dbt artifacts")
