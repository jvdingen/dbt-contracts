"""CLI entry point for dbt-contracts."""

import sys

import click

from dbt_contracts import __version__
from dbt_contracts.core.discovery import DiscoveryError, discover
from dbt_contracts.core.validation import validate


@click.group()
@click.version_option(version=__version__, prog_name="dbt-contracts")
def cli():
    """Generate and manage dbt projects through Bitol ODCS/ODPS data contracts."""


@cli.command()
def version():
    """Show the current version."""
    click.echo(f"dbt-contracts {__version__}")


@cli.command()
@click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to the contracts directory.",
    type=click.Path(),
)
def validate_cmd(contracts_dir):
    """Validate all contracts and products."""
    try:
        discovery = discover(contracts_dir)
    except DiscoveryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    n_contracts = len(discovery.contracts)
    n_products = len(discovery.products)
    click.echo(f"Discovered {n_contracts} contract(s) and {n_products} product(s).")

    result = validate(discovery)

    if result.passed:
        click.echo("Validation passed.")
    else:
        click.echo(f"Validation failed with {len(result.issues)} issue(s):\n")
        for issue in result.issues:
            location = issue.path
            if issue.contract_id:
                location = f"{issue.path} ({issue.contract_id})"
            click.echo(f"  {location}: {issue.message}")
        sys.exit(1)


# Register with the name 'validate' (validate_cmd avoids shadowing the import)
validate_cmd.name = "validate"
