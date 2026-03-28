"""CLI entry point for dbt-contracts."""

import click

from dbt_contracts import __version__


@click.group()
@click.version_option(version=__version__, prog_name="dbt-contracts")
def cli():
    """Generate and manage dbt projects through Bitol ODCS/ODPS data contracts."""


@cli.command()
def version():
    """Show the current version."""
    click.echo(f"dbt-contracts {__version__}")
