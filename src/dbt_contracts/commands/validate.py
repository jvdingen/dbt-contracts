"""Validate ODCS contracts."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from dbt_contracts.config import Config
from dbt_contracts.odcs.validator import lint_contract, test_contract


def run_validate(
    config: Config,
    project_root: Path,
    console: Console,
    *,
    contract: str | None = None,
    live: bool = False,
) -> bool:
    """Validate one or all ODCS contracts.

    Returns ``True`` if all contracts pass validation.
    """
    odcs_dir = project_root / config.paths.odcs_dir
    use_live = live or config.validation.default_mode == "test"

    if contract:
        contract_files = [Path(contract) if Path(contract).is_absolute() else odcs_dir / contract]
    else:
        if not odcs_dir.is_dir():
            console.print(f"[red]ODCS directory not found:[/red] {odcs_dir}")
            return False
        contract_files = sorted(odcs_dir.glob("**/*.odcs.yaml"))

    if not contract_files:
        console.print("[yellow]No ODCS contract files found.[/yellow]")
        return False

    all_passed = True
    for cf in contract_files:
        if not cf.is_file():
            console.print(f"[red]Contract file not found:[/red] {cf}")
            all_passed = False
            continue

        if use_live:
            passed, errors = test_contract(cf)
            mode_label = "TEST"
        else:
            passed, errors = lint_contract(cf)
            mode_label = "LINT"

        if passed:
            console.print(f"[green]PASSED[/green] [{mode_label}] {cf.name}")
        else:
            console.print(f"[red]FAILED[/red] [{mode_label}] {cf.name}")
            for err in errors:
                console.print(f"  [dim]{err}[/dim]")
            all_passed = False

    return all_passed
