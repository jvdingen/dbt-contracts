# CLI Reference

## Global options

```
dbt-contracts [OPTIONS] COMMAND
```

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to a specific config file (overrides auto-discovery) |
| `--verbose` | Enable verbose output |
| `--help` | Show help and exit |

## `init`

Scaffold a new project. Creates config file and directories. Safe to run multiple times -- skips existing files.

```sh
dbt-contracts init
```

## `generate`

Generate dbt artifacts from ODPS product definitions.

```sh
# Generate from all products
dbt-contracts generate

# Generate from one specific product file
dbt-contracts generate --product my_product.odps.yaml

# Preview what would be generated without writing files
dbt-contracts generate --dry-run
```

| Option | Description |
|--------|-------------|
| `--product FILE` | Generate from a specific ODPS file (name relative to `odps_dir`, or absolute path) |
| `--dry-run` | Preview without writing files |

Exit code is 1 if no files were generated (missing directories, no products found, etc.).

## `validate`

Validate ODCS contracts.

```sh
# Lint all contracts (default)
dbt-contracts validate

# Validate a specific contract
dbt-contracts validate --contract payments.odcs.yaml

# Run live tests against data sources (requires server configuration)
dbt-contracts validate --live
```

| Option | Description |
|--------|-------------|
| `--contract FILE` | Validate a specific ODCS file (name relative to `odcs_dir`, or absolute path) |
| `--live` | Run live data tests instead of offline lint |

Exit code is 1 if any contract fails validation.

## Interactive mode

Running `dbt-contracts` without a subcommand launches an interactive menu (when `cli_mode = "interactive"`, the default):

```
? What would you like to do?
  Initialize project
  Generate dbt artifacts
  Validate contracts
  Exit
```

The generate and validate flows prompt you to select specific files and options. Press Ctrl+C at any prompt to go back.

Set `cli_mode = "subcommand"` in your [configuration](configuration.md) to show help text instead.
