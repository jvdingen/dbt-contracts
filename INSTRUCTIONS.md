# Instructions

How to use `dbt-contracts` to generate dbt artifacts from ODPS data product definitions and ODCS data contracts.

## Prerequisites

- Python 3.12 or 3.13 (3.14 is not yet supported due to `duckdb` wheel availability)
- [pipx](https://pipx.pypa.io/stable/installation/) for global CLI installation

## Installation

Install `dbt-contracts` as a system-wide CLI tool:

```sh
pipx install dbt-contracts
```

If you have multiple Python versions and the default is 3.14+, specify 3.12 or 3.13 explicitly:

```sh
pipx install --python python3.12 dbt-contracts
```

To install from a local clone (for development or pre-release):

```sh
git clone <repo-url>
cd dbt-with-contracts
pipx install .
```

Verify the installation works:

```sh
dbt-contracts --help
```

### Development setup

If you want to contribute or run tests, use `uv` and `just` instead:

```sh
git clone <repo-url>
cd dbt-with-contracts
just install          # uv sync + pre-commit hooks
uv run dbt-contracts --help
```

## Quick Start

### 1. Initialize a project

```sh
dbt-contracts init
```

This creates:

- `dbt-contracts.toml` -- configuration file with commented-out defaults
- `contracts/products/` -- directory for ODPS product files
- `contracts/schemas/` -- directory for ODCS contract files
- `output/` -- directory for generated dbt artifacts

### 2. Add your contract files

Place ODPS data product definitions in `contracts/products/` using the `.odps.yaml` extension:

```yaml
# contracts/products/my_product.odps.yaml
apiVersion: v1.0.0
kind: DataProduct
name: Customer Data Product
id: fbe8d147-28db-4f1d-bedf-a3fe9f458427
domain: seller
status: draft

inputPorts:
  - name: payments
    version: 1.0.0
    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db

outputPorts:
  - name: customersummary
    description: Customer Summary
    type: tables
    version: 1.0.0
    contractId: a1234567-b890-cdef-1234-567890abcdef
    inputContracts:
      - id: dbb7b1eb-7628-436e-8914-2a00638ba6db
        version: 1.0.0
```

Place ODCS data contracts in `contracts/schemas/` using the `.odcs.yaml` extension:

```yaml
# contracts/schemas/payments.odcs.yaml
kind: DataContract
apiVersion: v3.1.0
id: dbb7b1eb-7628-436e-8914-2a00638ba6db
name: Payments Contract
version: 1.0.0
status: active

schema:
  - name: payments
    physicalName: raw_payments
    physicalType: table
    description: Payment transaction records
    properties:
      - name: payment_id
        logicalType: string
        physicalType: varchar
        primaryKey: true
        required: true
        description: Unique payment identifier
      - name: customer_id
        logicalType: string
        physicalType: varchar
        required: true
        description: Reference to the customer
      - name: amount
        logicalType: number
        physicalType: decimal
        required: true
        description: Payment amount in cents
```

```yaml
# contracts/schemas/customer_summary.odcs.yaml
kind: DataContract
apiVersion: v3.1.0
id: a1234567-b890-cdef-1234-567890abcdef
name: Customer Summary Contract
version: 1.0.0
status: active

schema:
  - name: customer_summary
    physicalName: customer_summary
    physicalType: table
    description: Aggregated customer metrics
    properties:
      - name: customer_id
        logicalType: string
        physicalType: varchar
        primaryKey: true
        required: true
        description: Unique customer identifier
      - name: total_payments
        logicalType: number
        physicalType: decimal
        required: true
        description: Total payment amount
      - name: last_payment_date
        logicalType: timestamp
        physicalType: timestamp
        required: false
        description: Date of most recent payment
```

Each ODPS port's `contractId` must match the `id` field of an ODCS contract file somewhere in the schemas directory. The tool searches recursively.

### 3. Generate dbt artifacts

```sh
dbt-contracts generate
```

This scans `contracts/products/` for `*.odps.yaml` files, resolves each port's `contractId` to an ODCS contract, and writes dbt artifacts to `output/`:

```
output/
├── sources.yml                         # from input ports
└── models/
    ├── schema.yml                      # from output ports
    └── staging/
        └── stg_customer_summary.sql    # staging SQL with source() refs
```

- **Input ports** become dbt sources -- the source name matches the port name.
- **Output ports** become dbt models with column definitions and tests.
- **Staging SQL** uses `{{ source('port_name', 'table') }}` refs, wired via the `inputContracts` lineage on output ports.

### 4. Validate contracts

```sh
dbt-contracts validate
```

This lints all `*.odcs.yaml` files in `contracts/schemas/` for structural correctness (offline, no database needed). Each contract gets a PASSED or FAILED result.

## CLI Reference

### Global options

```
dbt-contracts [OPTIONS] COMMAND
```

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to a specific config file (overrides auto-discovery) |
| `--verbose` | Enable verbose output |
| `--help` | Show help and exit |

### `init`

Scaffold a new project. Creates config file and directories. Safe to run multiple times -- it skips existing files and directories.

```sh
dbt-contracts init
```

### `generate`

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
| `--dry-run` | Show what would be generated without writing files |

Exit code is 1 if no files were generated (missing directories, no products found, etc.).

### `validate`

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

### Interactive mode

Running `dbt-contracts` without a subcommand launches an interactive menu (when `cli_mode` is set to `"interactive"`, which is the default):

```
? What would you like to do?
  Initialize project
  Generate dbt artifacts
  Validate contracts
  Exit
```

The generate and validate flows prompt you to select specific files and options. Press Ctrl+C at any prompt to go back.

## Configuration

Configuration is optional -- defaults work out of the box after `init`. The tool looks for configuration in this order:

1. Explicit `--config` flag
2. `dbt-contracts.toml` in the current directory
3. `[tool.dbt-contracts]` section in `pyproject.toml`
4. Built-in defaults

### Configuration file

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

# Where to write generated dbt artifacts
output_dir = "output"

[generation]
# Whether to overwrite existing output files
overwrite_existing = false

# When true, show what would be generated without writing files
dry_run = false

[validation]
# Default validation mode: "lint" (offline) or "test" (live, requires server)
default_mode = "lint"

# Whether to fail on validation errors
fail_on_error = false
```

All values shown above are the defaults. The `init` command creates a config file with everything commented out.

### pyproject.toml

You can also configure dbt-contracts inside your existing `pyproject.toml`:

```toml
[tool.dbt-contracts]
cli_mode = "subcommand"

[tool.dbt-contracts.paths]
odps_dir = "contracts/products"
odcs_dir = "contracts/schemas"
output_dir = "dbt_output"
```

If both `dbt-contracts.toml` and `pyproject.toml` exist, the standalone file takes precedence.

## How It Works

The tool connects two Bitol standards to dbt:

- [ODPS (Open Data Product Standard) v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) defines data products with input and output ports. Each port references a contract by `contractId`.
- [ODCS (Open Data Contract Standard) v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) defines the data schema (tables, columns, types), quality rules, and SLA properties.

The generation pipeline:

1. Parses the ODPS product file and extracts input/output ports
2. Resolves each port's `contractId` to an ODCS contract file
3. Exports dbt artifacts (sources, models, staging SQL) via `datacontract-cli`
4. Post-processes the output: renames sources to match port names, merges per-contract exports into single files, and rewires `source()` references using the `inputContracts` lineage

### File naming conventions

| Input file | Extension |
|------------|-----------|
| ODPS data products | `*.odps.yaml` |
| ODCS data contracts | `*.odcs.yaml` |

These extensions are required -- the tool uses them to discover files in the configured directories.

### ODPS to dbt mapping

| ODPS concept | dbt artifact |
|-------------|-------------|
| Input port | `sources.yml` entry (source name = port name) |
| Output port | `models/schema.yml` entry (model + column definitions) |
| Output port with schema | `models/staging/stg_<table>.sql` (staging SQL) |
| `inputContracts` on output port | `{{ source() }}` refs in staging SQL |

## Troubleshooting

**"ODPS directory not found"** -- Run `dbt-contracts init` first, or check the `odps_dir` path in your config.

**"No ODPS product files found"** -- Make sure your product files use the `.odps.yaml` extension and are inside the configured `odps_dir`.

**"Contract not found"** -- The `contractId` in your ODPS port doesn't match the `id` field of any `.odcs.yaml` file in `odcs_dir`. Check that both UUIDs match exactly.

**"Invalid configuration"** -- Your config file has an unrecognized key. The tool rejects typos to prevent silent misconfiguration. Check spelling against the configuration reference above.

**Validation FAILED** -- Run `dbt-contracts validate` to see which contracts fail and why. The error messages come from `datacontract-cli`'s lint checks. Common issues: missing required fields (`id`, `version`, `status`), invalid `apiVersion`, or malformed schema.
