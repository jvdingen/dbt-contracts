"""Tests for the CLI entry point."""

from dbt_contracts import __version__
from dbt_contracts.cli import cli


def test_version_command(runner):
    """The version command prints the current version."""
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_option(runner):
    """The --version flag prints the version."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help(runner):
    """The --help flag shows usage information."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "dbt projects" in output or "data contracts" in output
