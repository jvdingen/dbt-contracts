"""CLI entry point for dbt-contracts."""

import sys
from pathlib import Path

import click

from dbt_contracts import __version__
from dbt_contracts.core.differ import diff
from dbt_contracts.core.discovery import DiscoveryError, DiscoveryResult, discover
from dbt_contracts.core.generator import generate
from dbt_contracts.core.importer import import_dbt
from dbt_contracts.core.init import init
from dbt_contracts.core.validation import validate
from dbt_contracts.models.config import Config

# Reusable CLI options
contracts_dir_option = click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to the contracts directory.",
    type=click.Path(),
)
models_dir_option = click.option(
    "--models-dir",
    default=None,
    help="Override models output directory.",
)
sources_dir_option = click.option(
    "--sources-dir",
    default=None,
    help="Override sources output directory.",
)


def _discover_or_exit(contracts_dir: str) -> DiscoveryResult:
    """Run discovery, exiting on error."""
    try:
        return discover(contracts_dir)
    except DiscoveryError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _resolve_output_base(contracts_dir: str, config: Config) -> Path:
    """Resolve the dbt project root from contracts dir and config."""
    return Path(contracts_dir) / (config.dbt_project_dir or "..")


def _print_validation_errors(result) -> None:
    """Print validation issues and exit."""
    click.echo(f"Validation failed with {len(result.issues)} issue(s):\n")
    for issue in result.issues:
        location = issue.path
        if issue.contract_id:
            location = f"{issue.path} ({issue.contract_id})"
        click.echo(f"  {location}: {issue.message}")
    sys.exit(1)


@click.group()
@click.version_option(version=__version__, prog_name="dbt-contracts")
def cli():
    """Generate and manage dbt projects through Bitol ODCS/ODPS data contracts."""


@cli.command()
def version():
    """Show the current version."""
    click.echo(f"dbt-contracts {__version__}")


@cli.command("validate")
@contracts_dir_option
def validate_cmd(contracts_dir):
    """Validate all contracts and products."""
    discovery = _discover_or_exit(contracts_dir)

    n_contracts = len(discovery.contracts)
    n_products = len(discovery.products)
    click.echo(f"Discovered {n_contracts} contract(s) and {n_products} product(s).")

    result = validate(discovery)

    if result.passed:
        click.echo("Validation passed.")
    else:
        _print_validation_errors(result)


@cli.command("generate")
@contracts_dir_option
@models_dir_option
@sources_dir_option
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite non-managed files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview without writing files.",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip validation before generating.",
)
def generate_cmd(
    contracts_dir, models_dir, sources_dir, force, dry_run, skip_validation
):
    """Generate dbt models, sources, and SQL from contracts."""
    discovery = _discover_or_exit(contracts_dir)

    if not skip_validation:
        result = validate(discovery)
        if not result.passed:
            _print_validation_errors(result)

    output_base = _resolve_output_base(contracts_dir, discovery.config)

    gen_result = generate(
        discovery,
        output_base=output_base,
        models_dir=models_dir,
        sources_dir=sources_dir,
        force=force,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("Dry run — no files written.\n")
        for f in gen_result.files:
            click.echo(f"--- {f.path} ---")
            click.echo(f.content)
    else:
        for f in gen_result.files:
            if f.skipped:
                click.echo(f"Skipped (not managed): {f.path}")
            else:
                click.echo(f"Written: {f.path}")
        click.echo(
            f"\n{len(gen_result.written)} file(s) written, "
            f"{len(gen_result.skipped_files)} skipped."
        )


@cli.command("init")
@click.option(
    "--dir",
    "target_dir",
    default=".",
    help="Directory where contracts/ will be created.",
    type=click.Path(),
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing contracts/ directory.",
)
def init_cmd(target_dir, force):
    """Initialize a contracts/ directory with default configuration."""
    result = init(Path(target_dir), force=force)

    if not result.created:
        click.echo(
            f"contracts/ already exists at {result.contracts_dir}. "
            "Use --force to overwrite."
        )
        sys.exit(1)

    click.echo(f"Initialized contracts/ at {result.contracts_dir}")
    if result.config_path:
        click.echo(f"  Config: {result.config_path}")
    click.echo(
        "\nNext steps:\n"
        "  1. Add ODCS contracts to contracts/contracts/\n"
        "  2. Add ODPS products to contracts/products/\n"
        "  3. Run: dbt-contracts validate"
    )


@cli.command("diff")
@contracts_dir_option
@models_dir_option
@sources_dir_option
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format.",
)
def diff_cmd(contracts_dir, models_dir, sources_dir, output_format):
    """Show drift between contracts and the current dbt project."""
    discovery = _discover_or_exit(contracts_dir)
    output_base = _resolve_output_base(contracts_dir, discovery.config)

    result = diff(
        discovery,
        output_base=output_base,
        models_dir=models_dir,
        sources_dir=sources_dir,
    )

    if output_format == "json":
        import json

        click.echo(
            json.dumps(
                [{"path": str(d.path), "status": d.status.value} for d in result.diffs],
                indent=2,
            )
        )
    else:
        for d in result.diffs:
            click.echo(f"  [{d.status.value}] {d.path}")
        click.echo(
            f"\n{len(result.new_files)} new, "
            f"{len(result.modified_files)} modified, "
            f"{len(result.unchanged_files)} unchanged."
        )

    if result.has_drift:
        sys.exit(1)


@cli.command("sync")
@contracts_dir_option
@models_dir_option
@sources_dir_option
@click.option(
    "--yes",
    is_flag=True,
    help="Apply changes without confirmation.",
)
def sync_cmd(contracts_dir, models_dir, sources_dir, yes):
    """Sync dbt project with contracts (apply diff)."""
    discovery = _discover_or_exit(contracts_dir)
    output_base = _resolve_output_base(contracts_dir, discovery.config)

    result = diff(
        discovery,
        output_base=output_base,
        models_dir=models_dir,
        sources_dir=sources_dir,
    )

    if not result.has_drift:
        click.echo("No drift detected. Nothing to sync.")
        return

    click.echo("Changes to apply:")
    for d in result.new_files:
        click.echo(f"  [new] {d.path}")
    for d in result.modified_files:
        click.echo(f"  [modified] {d.path}")

    if not yes:
        click.confirm("Apply these changes?", abort=True)

    # Write files directly from diff result instead of re-running generate
    written = 0
    for d in result.new_files + result.modified_files:
        d.path.parent.mkdir(parents=True, exist_ok=True)
        d.path.write_text(d.expected_content, encoding="utf-8")
        written += 1

    click.echo(f"\n{written} file(s) written.")


@cli.command("import")
@click.argument(
    "schema_files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    "--output-dir",
    default="contracts/contracts",
    help="Directory for generated contract files.",
    type=click.Path(),
)
@click.option(
    "--server-type",
    default="snowflake",
    help="Default server type for contracts.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview without writing files.",
)
def import_cmd(schema_files, output_dir, server_type, dry_run):
    """Generate ODCS contracts from existing dbt schema YAML files."""
    paths = [Path(f) for f in schema_files]

    result = import_dbt(
        paths,
        output_dir=Path(output_dir),
        server_type=server_type,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("Dry run — no files written.\n")
        for c in result.contracts:
            click.echo(f"--- {c.path} ---")
            click.echo(c.content)
    else:
        for c in result.contracts:
            click.echo(f"Written: {c.path}")
        click.echo(f"\n{len(result.contracts)} contract(s) generated.")
