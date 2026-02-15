"""Config command — inspect and update dbt-contracts configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w
from rich.console import Console

from dbt_contracts.config import SETTINGS, SETTINGS_BY_KEY, Config, Setting, find_config_path


def run_config_show(config: Config, console: Console) -> None:
    """Print the resolved configuration as TOML."""
    data = config.model_dump()
    console.print(tomli_w.dumps(data))


def run_config_path(project_root: Path, console: Console, config_path: Path | None = None) -> None:
    """Print the active config file path, or 'none'."""
    resolved = find_config_path(config_path=config_path, project_root=project_root)
    if resolved is None:
        console.print("No config file found (using defaults)")
    else:
        console.print(str(resolved))


def run_config_set(key: str, value: str, project_root: Path, console: Console) -> bool:
    """Set a config value in dbt-contracts.toml.

    Returns ``True`` on success, ``False`` on validation error.
    """
    setting = SETTINGS_BY_KEY.get(key)
    if setting is None:
        console.print(f'[red]Error:[/red] Unknown key "{key}"\n')
        _print_available_keys(console)
        return False

    try:
        coerced = _coerce_value(value, setting)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return False

    toml_path = project_root / "dbt-contracts.toml"
    if toml_path.is_file():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    # Set value at the correct nesting level
    parts = key.split(".")
    target = data
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = coerced

    # Validate before writing
    Config(**data)

    toml_path.write_bytes(tomli_w.dumps(data).encode())
    console.print(f"[green]Set[/green] {key} = {_display_value(coerced)}")
    return True


def run_config_export(config: Config, path: Path, console: Console) -> bool:
    """Export the resolved configuration to a TOML file.

    Returns ``True`` on success.
    """
    data = config.model_dump()
    path.write_bytes(tomli_w.dumps(data).encode())
    console.print(f"[green]Exported[/green] configuration to {path}")
    return True


def run_config_import(path: Path, project_root: Path, console: Console) -> bool:
    """Import configuration from a TOML file into dbt-contracts.toml.

    Validates the file before writing. Returns ``True`` on success.
    """
    with open(path, "rb") as f:
        data = tomllib.load(f)

    Config(**data)

    toml_path = project_root / "dbt-contracts.toml"
    toml_path.write_bytes(tomli_w.dumps(data).encode())
    console.print(f"[green]Imported[/green] configuration from {path}")
    return True


_BOOL_TRUE = {"true", "yes", "1"}
_BOOL_FALSE = {"false", "no", "0"}


def _coerce_value(value: str, setting: Setting) -> bool | str:
    """Coerce a string value to the appropriate Python type.

    Raises:
        ValueError: If the value cannot be coerced to the expected type.
    """
    if setting.type == "bool":
        lower = value.lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        msg = f'"{setting.key}" must be true or false'
        raise ValueError(msg)

    # String type — check constrained choices if any
    if setting.choices and value not in setting.choices:
        choices_str = ", ".join(setting.choices)
        msg = f'"{setting.key}" must be one of: {choices_str}'
        raise ValueError(msg)

    return value


def _display_value(value: object) -> str:
    """Format a value for display."""
    if isinstance(value, bool):
        return str(value).lower()
    return f'"{value}"'


def _print_available_keys(console: Console) -> None:
    """Print grouped help text for all available config keys."""
    console.print("Available keys:")

    current_group = None
    for setting in SETTINGS:
        group = setting.key.split(".")[0] if "." in setting.key else None

        # Add blank line between groups
        if group != current_group:
            console.print()
            current_group = group

        console.print(f"  {setting.key:<32}{setting.description}")
