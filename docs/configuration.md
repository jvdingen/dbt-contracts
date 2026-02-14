# Configuration

Configuration is optional -- defaults work out of the box after `dbt-contracts init`.

## Resolution order

The tool looks for configuration in this order:

1. Explicit `--config` flag
2. `dbt-contracts.toml` in the current directory
3. `[tool.dbt-contracts]` section in `pyproject.toml`
4. Built-in defaults

## Config file reference

```toml
# dbt-contracts.toml

# How the CLI behaves when run without a subcommand.
# "interactive" = show menu, "subcommand" = show help text.
cli_mode = "interactive"

[paths]
# Where to find ODPS product definitions (searched recursively for *.odps.yaml)
odps_dir = "contracts/products"

# Where to find ODCS contract files (searched recursively for *.odcs.yaml)
odcs_dir = "contracts/schemas"

# Where to write generated dbt models (schema.yml, staging SQL)
models_dir = "models"

# Where to write generated dbt source definitions (sources.yml)
sources_dir = "sources"

[generation]
# When true, show what would be generated without writing files
dry_run = false

[validation]
# Default validation mode: "lint" (offline) or "test" (live, requires server)
default_mode = "lint"

# Whether to fail on validation errors
fail_on_error = false
```

All values shown above are the defaults. The `init` command creates a config file with everything commented out.

## Using pyproject.toml

You can configure `dbt-contracts` inside your existing `pyproject.toml` instead of a standalone file:

```toml
[tool.dbt-contracts]
cli_mode = "subcommand"

[tool.dbt-contracts.paths]
odps_dir = "contracts/products"
odcs_dir = "contracts/schemas"
models_dir = "models"
sources_dir = "sources"
```

!!! info "Precedence"
    If both `dbt-contracts.toml` and `pyproject.toml` exist, the standalone file takes precedence.
