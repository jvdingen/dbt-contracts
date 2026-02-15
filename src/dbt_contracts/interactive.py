"""Interactive menu-driven mode for dbt-contracts."""

from __future__ import annotations

from pathlib import Path

import questionary
from rich.console import Console

from dbt_contracts.commands.config import run_config_export, run_config_import, run_config_set, run_config_show
from dbt_contracts.commands.generate import run_generate
from dbt_contracts.commands.init import run_init
from dbt_contracts.commands.validate import run_validate
from dbt_contracts.config import SETTINGS, Config, load_config


def run_interactive(config: Config, project_root: Path, console: Console) -> None:
    """Run the interactive menu loop.

    Presents a questionary select menu and delegates to the appropriate
    ``run_*`` command function.  Handles ``None`` returns (Ctrl+C) gracefully.
    """
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Initialize project",
                "Generate dbt artifacts",
                "Validate contracts",
                "Configuration",
                "Exit",
            ],
        ).ask()

        if choice is None or choice == "Exit":
            break

        console.print()

        if choice == "Initialize project":
            run_init(project_root, console)

        elif choice == "Generate dbt artifacts":
            config = _generate_flow(config, project_root, console)

        elif choice == "Validate contracts":
            _validate_flow(config, project_root, console)

        elif choice == "Configuration":
            config = _config_flow(config, project_root, console)

        console.print()


def _config_flow(config: Config, project_root: Path, console: Console) -> Config:
    """Interactive sub-menu for configuration."""
    choice = questionary.select(
        "Configuration",
        choices=["Show current configuration", "Edit a setting", "Export to file", "Import from file", "Back"],
    ).ask()

    if choice is None or choice == "Back":
        return config

    if choice == "Show current configuration":
        run_config_show(config, console)

    elif choice == "Edit a setting":
        config = _config_edit_flow(config, project_root, console)

    elif choice == "Export to file":
        config = _config_export_flow(config, console)

    elif choice == "Import from file":
        config = _config_import_flow(project_root, console)

    return config


def _config_export_flow(config: Config, console: Console) -> Config:
    """Interactive sub-flow for exporting configuration to a file."""
    path = questionary.path("Export to", default="contracts/dbt-contracts.toml").ask()
    if path is None:
        return config
    run_config_export(config, Path(path), console)
    return config


def _config_import_flow(project_root: Path, console: Console) -> Config:
    """Interactive sub-flow for importing configuration from a file."""
    path = questionary.path("Import from").ask()
    if path is None:
        return load_config(project_root=project_root)

    target = Path(path)
    if not target.is_file():
        console.print(f"[red]Error:[/red] File not found: {target}")
        return load_config(project_root=project_root)

    run_config_import(target, project_root, console)
    return load_config(project_root=project_root)


def _ask_setting_value(setting_key: str, setting_type: str, choices: tuple[str, ...] | None, current: str | bool) -> str | None:
    """Prompt for a new setting value. Returns the string representation, or None if cancelled."""
    if setting_type == "bool":
        assert isinstance(current, bool)
        result = questionary.confirm(f"{setting_key}", default=current).ask()
        if result is None:
            return None
        return "true" if result else "false"

    if choices:
        assert isinstance(current, str)
        return questionary.select(f"{setting_key}", choices=list(choices), default=current).ask()

    return questionary.text(f"{setting_key}", default=str(current)).ask()


def _config_edit_flow(config: Config, project_root: Path, console: Console) -> Config:
    """Interactive sub-flow for editing a configuration value."""
    menu_choices = [
        questionary.Choice(
            f"{s.key}  ({_format_current(config, s.key)})",
            value=s.key,
        )
        for s in SETTINGS
    ]
    selected_key = questionary.select("Which setting?", choices=menu_choices).ask()
    if selected_key is None:
        return config

    setting = next(s for s in SETTINGS if s.key == selected_key)
    current = _get_current_value(config, selected_key)

    value_str = _ask_setting_value(selected_key, setting.type, setting.choices, current)
    if value_str is None:
        return config

    if run_config_set(selected_key, value_str, project_root, console):
        return load_config(project_root=project_root)
    return config


def _get_current_value(config: Config, dotted_key: str) -> str | bool:
    """Resolve a dotted key against the current Config."""
    parts = dotted_key.split(".")
    obj: object = config
    for part in parts:
        obj = getattr(obj, part)
    assert isinstance(obj, (str, bool))
    return obj


def _format_current(config: Config, dotted_key: str) -> str:
    """Format the current value of a setting for display in the menu."""
    value = _get_current_value(config, dotted_key)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _generate_flow(config: Config, project_root: Path, console: Console) -> Config:
    """Interactive sub-flow for generating dbt artifacts."""
    odps_dir = project_root / config.paths.odps_dir
    products = sorted(odps_dir.glob("**/*.odps.yaml")) if odps_dir.is_dir() else []

    product = None
    if products:
        choices = ["All products"] + [p.name for p in products]
        selected = questionary.select("Which product?", choices=choices).ask()
        if selected is None:
            return config
        if selected != "All products":
            product = selected

    dry_run_answer = questionary.confirm("Dry run?", default=False).ask()
    if dry_run_answer is None:
        return config

    run_generate(config, project_root, console, product=product, dry_run=dry_run_answer, interactive=True)
    return config


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
