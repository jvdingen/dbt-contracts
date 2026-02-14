"""Generate dbt artifacts from ODPS product definitions."""

from __future__ import annotations

import difflib
from pathlib import Path

import questionary
from rich.console import Console

from dbt_contracts.config import Config
from dbt_contracts.generators.orchestrator import DriftStatus, GeneratedFile, plan_for_product, write_files


def run_generate(
    config: Config,
    project_root: Path,
    console: Console,
    *,
    product: str | None = None,
    dry_run: bool = False,
    yolo_mode: bool = False,
    interactive: bool = False,
) -> bool:
    """Generate dbt artifacts for one or all ODPS products.

    Returns ``True`` if any files were generated, ``False`` otherwise.
    """
    odps_dir = project_root / config.paths.odps_dir
    odcs_dir = project_root / config.paths.odcs_dir
    models_dir = project_root / config.paths.models_dir
    sources_dir = project_root / config.paths.sources_dir
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

        planned = plan_for_product(pf, odcs_dir, models_dir, sources_dir)
        if not planned:
            console.print(f"[yellow]No output for[/yellow] {pf.name}")
            continue

        new_files = [f for f in planned if f.drift_status == DriftStatus.NEW]
        unchanged_files = [f for f in planned if f.drift_status == DriftStatus.UNCHANGED]
        changed_files = [f for f in planned if f.drift_status == DriftStatus.CHANGED]

        # Report unchanged files
        for f in unchanged_files:
            console.print(f"[dim]Unchanged[/dim] {f.path}")

        # Write new files directly
        if new_files:
            write_files(new_files)
            any_generated = True
            for f in new_files:
                console.print(f"[green]Created[/green] {f.path}")

        # Handle changed files
        if changed_files:
            if effective_dry_run:
                for f in changed_files:
                    _show_drift_summary(f, console)
                any_generated = True
            elif yolo_mode and not interactive:
                write_files(changed_files)
                any_generated = True
                for f in changed_files:
                    console.print(f"[green]Updated[/green] {f.path}")
            else:
                written = _prompt_changed_files(changed_files, console)
                if written:
                    any_generated = True

        if not changed_files and not new_files and unchanged_files:
            any_generated = True

    return any_generated


def _show_drift_summary(gen_file: GeneratedFile, console: Console) -> None:
    """Show a unified diff for a changed file."""
    existing = gen_file.path.read_text().splitlines(keepends=True)
    proposed = gen_file.content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        existing,
        proposed,
        fromfile=str(gen_file.path),
        tofile=str(gen_file.path) + " (new)",
    )
    console.print(f"\n[bold]Drift detected:[/bold] {gen_file.path}")
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+") and not line.startswith("+++"):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("-") and not line.startswith("---"):
            console.print(f"[red]{line}[/red]")
        else:
            console.print(line)


def _prompt_changed_files(changed: list[GeneratedFile], console: Console) -> list[Path]:
    """Prompt per-file for changed files. Returns paths that were written."""
    written: list[Path] = []
    accept_all = False

    for f in changed:
        if accept_all:
            f.path.parent.mkdir(parents=True, exist_ok=True)
            f.path.write_text(f.content)
            written.append(f.path)
            console.print(f"[green]Updated[/green] {f.path}")
            continue

        _show_drift_summary(f, console)
        answer = questionary.select(
            f"Apply changes to {f.path.name}?",
            choices=["Yes", "No", "Yes to all remaining"],
        ).ask()

        if answer is None:
            break
        elif answer == "Yes":
            f.path.parent.mkdir(parents=True, exist_ok=True)
            f.path.write_text(f.content)
            written.append(f.path)
            console.print(f"[green]Updated[/green] {f.path}")
        elif answer == "Yes to all remaining":
            accept_all = True
            f.path.parent.mkdir(parents=True, exist_ok=True)
            f.path.write_text(f.content)
            written.append(f.path)
            console.print(f"[green]Updated[/green] {f.path}")
        # "No" → skip

    return written
