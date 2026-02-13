"""Tests for the project's entry point and CLI structure."""

import click

from dbt_contracts import cli as cli_module


def test_main_is_callable() -> None:
    """The main entry point is a callable function."""
    assert callable(cli_module.main)


def test_cli_is_click_group() -> None:
    """The cli object is a Click group."""
    assert isinstance(cli_module.cli, click.Group)


def test_cli_has_expected_commands() -> None:
    """The CLI group has init, generate, and validate subcommands."""
    commands = set(cli_module.cli.commands)
    assert {"init", "generate", "validate"} <= commands
