"""Command-line entry points for dbt-contracts."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import logfire
from pydantic import ValidationError
from rich.console import Console

from dbt_contracts.config import load_config

# 'if-token-present' means nothing will be sent (and the example still works)
# when a Logfire token/environment isn't configured.
logfire.configure(send_to_logfire="if-token-present")


@click.group(invoke_without_command=True)
@click.option(
    "--config", "config_path", type=click.Path(exists=True, path_type=Path), default=None, help="Path to config file."
)
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, config_path: Path | None, verbose: bool) -> None:
    """Contract-driven dbt workflow using ODPS and ODCS."""
    console = Console()
    project_root = Path.cwd()

    try:
        config = load_config(config_path=config_path, project_root=project_root)
    except ValidationError as exc:
        console.print(f"[red]Invalid configuration:[/red] {exc}")
        sys.exit(1)

    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["project_root"] = project_root
    ctx.obj["console"] = console
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        if config.cli_mode == "interactive":
            from dbt_contracts.interactive import run_interactive

            run_interactive(config, project_root, console)
        else:
            click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--adapter",
    type=click.Choice(["duckdb", "postgres", "snowflake", "bigquery"]),
    default=None,
    help="Database adapter for profiles.yml.",
)
@click.pass_context
def init(ctx: click.Context, adapter: str | None) -> None:
    """Initialize a new dbt-contracts project."""
    from dbt_contracts.commands.init import run_init

    run_init(ctx.obj["project_root"], ctx.obj["console"], adapter=adapter)


@cli.command()
@click.option("--product", default=None, help="Specific ODPS product file to generate from.")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be generated without writing files.")
@click.pass_context
def generate(ctx: click.Context, product: str | None, dry_run: bool) -> None:
    """Generate dbt artifacts from ODPS product definitions."""
    from dbt_contracts.commands.generate import run_generate

    success = run_generate(
        ctx.obj["config"],
        ctx.obj["project_root"],
        ctx.obj["console"],
        product=product,
        dry_run=dry_run,
    )
    if not success:
        sys.exit(1)


@cli.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """Inspect and manage dbt-contracts configuration."""
    if ctx.invoked_subcommand is None:
        from dbt_contracts.commands.config import run_config_show

        run_config_show(ctx.obj["config"], ctx.obj["console"])


@config.command("path")
@click.pass_context
def config_path(ctx: click.Context) -> None:
    """Show the active config file path."""
    from dbt_contracts.commands.config import run_config_path

    run_config_path(ctx.obj["project_root"], ctx.obj["console"])


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value in dbt-contracts.toml."""
    from dbt_contracts.commands.config import run_config_set

    success = run_config_set(key, value, ctx.obj["project_root"], ctx.obj["console"])
    if not success:
        sys.exit(1)


@config.command("export")
@click.argument("path", type=click.Path(path_type=Path))
@click.pass_context
def config_export(ctx: click.Context, path: Path) -> None:
    """Export resolved configuration to a TOML file."""
    from dbt_contracts.commands.config import run_config_export

    run_config_export(ctx.obj["config"], path, ctx.obj["console"])


@config.command("import")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def config_import(ctx: click.Context, path: Path) -> None:
    """Import configuration from a TOML file into dbt-contracts.toml."""
    from dbt_contracts.commands.config import run_config_import

    success = run_config_import(path, ctx.obj["project_root"], ctx.obj["console"])
    if not success:
        sys.exit(1)


@cli.command()
@click.option("--contract", default=None, help="Specific ODCS contract file to validate.")
@click.option("--live", is_flag=True, default=False, help="Run live tests against data sources.")
@click.pass_context
def validate(ctx: click.Context, contract: str | None, live: bool) -> None:
    """Validate ODCS contracts."""
    from dbt_contracts.commands.validate import run_validate

    success = run_validate(
        ctx.obj["config"],
        ctx.obj["project_root"],
        ctx.obj["console"],
        contract=contract,
        live=live,
    )
    if not success:
        sys.exit(1)


def main() -> None:
    """Entry point for the dbt-contracts CLI."""
    logfire.info("application.startup")
    cli()
