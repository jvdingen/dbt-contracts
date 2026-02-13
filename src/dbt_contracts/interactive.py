"""Interactive menu-driven mode for dbt-contracts."""

from __future__ import annotations

from pathlib import Path

import questionary
from rich.console import Console

from dbt_contracts.commands.generate import run_generate
from dbt_contracts.commands.init import run_init
from dbt_contracts.commands.validate import run_validate
from dbt_contracts.config import Config


def run_interactive(config: Config, project_root: Path, console: Console) -> None:
    """Run the interactive menu loop.

    Presents a questionary select menu and delegates to the appropriate
    ``run_*`` command function.  Handles ``None`` returns (Ctrl+C) gracefully.
    """
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Initialize project", "Generate dbt artifacts", "Validate contracts", "Exit"],
        ).ask()

        if choice is None or choice == "Exit":
            break

        console.print()

        if choice == "Initialize project":
            run_init(project_root, console)

        elif choice == "Generate dbt artifacts":
            _generate_flow(config, project_root, console)

        elif choice == "Validate contracts":
            _validate_flow(config, project_root, console)

        console.print()


def _generate_flow(config: Config, project_root: Path, console: Console) -> None:
    """Interactive sub-flow for generating dbt artifacts."""
    odps_dir = project_root / config.paths.odps_dir
    products = sorted(odps_dir.glob("**/*.odps.yaml")) if odps_dir.is_dir() else []

    product = None
    if products:
        choices = ["All products"] + [p.name for p in products]
        selected = questionary.select("Which product?", choices=choices).ask()
        if selected is None:
            return
        if selected != "All products":
            product = selected

    dry_run_answer = questionary.confirm("Dry run?", default=False).ask()
    if dry_run_answer is None:
        return

    run_generate(config, project_root, console, product=product, dry_run=dry_run_answer)


def _validate_flow(config: Config, project_root: Path, console: Console) -> None:
    """Interactive sub-flow for validating contracts."""
    odcs_dir = project_root / config.paths.odcs_dir
    contracts = sorted(odcs_dir.glob("**/*.odcs.yaml")) if odcs_dir.is_dir() else []

    contract = None
    if contracts:
        choices = ["All contracts"] + [c.name for c in contracts]
        selected = questionary.select("Which contract?", choices=choices).ask()
        if selected is None:
            return
        if selected != "All contracts":
            contract = selected

    live_answer = questionary.confirm("Run live tests?", default=False).ask()
    if live_answer is None:
        return

    run_validate(config, project_root, console, contract=contract, live=live_answer)
