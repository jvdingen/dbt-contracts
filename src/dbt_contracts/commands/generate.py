"""Generate dbt artifacts from ODPS product definitions."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from dbt_contracts.config import Config
from dbt_contracts.generators.orchestrator import generate_for_product


def run_generate(
    config: Config,
    project_root: Path,
    console: Console,
    *,
    product: str | None = None,
    dry_run: bool = False,
) -> bool:
    """Generate dbt artifacts for one or all ODPS products.

    Returns ``True`` if any files were generated, ``False`` otherwise.
    """
    odps_dir = project_root / config.paths.odps_dir
    odcs_dir = project_root / config.paths.odcs_dir
    output_dir = project_root / config.paths.output_dir
    effective_dry_run = dry_run or config.generation.dry_run

    if product:
        product_files = [Path(product) if Path(product).is_absolute() else odps_dir / product]
    else:
        if not odps_dir.is_dir():
            console.print(f"[red]ODPS directory not found:[/red] {odps_dir}")
            return False
        product_files = sorted(odps_dir.glob("**/*.odps.yaml"))

    if not product_files:
        console.print("[yellow]No ODPS product files found.[/yellow]")
        return False

    any_generated = False
    for pf in product_files:
        if not pf.is_file():
            console.print(f"[red]Product file not found:[/red] {pf}")
            continue

        if effective_dry_run:
            console.print(f"[dim]Dry run:[/dim] would generate from {pf.name}")
            any_generated = True
            continue

        written = generate_for_product(pf, odcs_dir, output_dir)
        if written:
            any_generated = True
            for path in written:
                console.print(f"[green]Generated[/green] {path}")
        else:
            console.print(f"[yellow]No output for[/yellow] {pf.name}")

    return any_generated
