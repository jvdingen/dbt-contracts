# dbt-contracts

Contract-driven dbt workflow tool using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) and [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) to generate dbt models, sources, and tests.

## Installation

```sh
pipx install dbt-contracts
```

If your default Python is 3.14+, specify an earlier version:

```sh
pipx install --python python3.12 dbt-contracts
```

Verify:

```sh
dbt-contracts --help
```

## Quick Start

### 1. Initialize a project

```sh
dbt-contracts init
```

Creates the following structure:

- `dbt-contracts.toml` -- configuration file
- `contracts/products/` -- ODPS product definitions
- `contracts/schemas/` -- ODCS contract files
- `output/` -- generated dbt artifacts

### 2. Add contract files

Place ODPS data product definitions in `contracts/products/` (`.odps.yaml`):

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

Place ODCS contracts in `contracts/schemas/` (`.odcs.yaml`):

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
      - name: customer_id
        logicalType: string
        physicalType: varchar
        required: true
      - name: amount
        logicalType: number
        physicalType: decimal
        required: true
```

Each port's `contractId` must match the `id` field of an ODCS file in the schemas directory.

### 3. Generate dbt artifacts

```sh
dbt-contracts generate
```

Produces:

```
output/
├── sources.yml                         # from input ports
└── models/
    ├── schema.yml                      # from output ports
    └── staging/
        └── stg_customer_summary.sql    # staging SQL with source() refs
```

- **Input ports** become dbt sources (source name = port name)
- **Output ports** become dbt models with column definitions and tests
- **Staging SQL** uses `{{ source('port_name', 'table') }}` refs via `inputContracts` lineage

### 4. Validate contracts

```sh
dbt-contracts validate
```

Lints all `.odcs.yaml` files for structural correctness (offline, no database needed).

## CLI Reference

### Global options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to a specific config file (overrides auto-discovery) |
| `--verbose` | Enable verbose output |
| `--help` | Show help and exit |

### `init`

Scaffold a new project. Safe to run multiple times -- skips existing files.

```sh
dbt-contracts init
```

### `generate`

Generate dbt artifacts from ODPS product definitions.

```sh
dbt-contracts generate
dbt-contracts generate --product my_product.odps.yaml
dbt-contracts generate --dry-run
```

| Option | Description |
|--------|-------------|
| `--product FILE` | Generate from a specific ODPS file |
| `--dry-run` | Preview without writing files |

### `validate`

Validate ODCS contracts.

```sh
dbt-contracts validate
dbt-contracts validate --contract payments.odcs.yaml
dbt-contracts validate --live
```

| Option | Description |
|--------|-------------|
| `--contract FILE` | Validate a specific ODCS file |
| `--live` | Run live data tests (requires server configuration) |

### Interactive mode

Running `dbt-contracts` without a subcommand launches an interactive menu (when `cli_mode = "interactive"`, the default).

## Configuration

Configuration is optional -- defaults work out of the box after `init`. Resolution order:

1. Explicit `--config` flag
2. `dbt-contracts.toml` in the current directory
3. `[tool.dbt-contracts]` in `pyproject.toml`
4. Built-in defaults

### Config file reference

```toml
# dbt-contracts.toml

cli_mode = "interactive"    # "interactive" or "subcommand"

[paths]
odps_dir = "contracts/products"
odcs_dir = "contracts/schemas"
output_dir = "output"

[generation]
overwrite_existing = false
dry_run = false

[validation]
default_mode = "lint"       # "lint" or "test"
fail_on_error = false
```

All values above are defaults. You can also use `[tool.dbt-contracts]` in `pyproject.toml`.

## How It Works

The tool connects two [Bitol](https://bitol.io/) standards to dbt:

- **ODPS** defines data products with input/output ports, each referencing a contract by `contractId`
- **ODCS** defines data schemas (tables, columns, types), quality rules, and SLA properties

The generation pipeline:

1. Parse ODPS product files and extract input/output ports
2. Resolve each port's `contractId` to an ODCS contract file
3. Export dbt artifacts (sources, models, staging SQL) via `datacontract-cli`
4. Post-process: rename sources to match port names, merge exports, rewire `source()` references using `inputContracts` lineage

### ODPS to dbt mapping

| ODPS concept | dbt artifact |
|-------------|-------------|
| Input port | `sources.yml` entry |
| Output port | `models/schema.yml` entry |
| Output port with schema | `models/staging/stg_<table>.sql` |
| `inputContracts` on output port | `{{ source() }}` refs in staging SQL |

## Troubleshooting

| Error | Fix |
|-------|-----|
| "ODPS directory not found" | Run `dbt-contracts init` or check `odps_dir` in config |
| "No ODPS product files found" | Ensure files use `.odps.yaml` extension in `odps_dir` |
| "Contract not found" | `contractId` doesn't match any `.odcs.yaml` `id` field |
| "Invalid configuration" | Unrecognized config key -- check spelling |
| Validation FAILED | Run `dbt-contracts validate` for details |

## API Reference

::: dbt_contracts.config

::: dbt_contracts.commands.init

::: dbt_contracts.commands.generate

::: dbt_contracts.commands.validate

::: dbt_contracts.interactive

::: dbt_contracts.odps.schema

::: dbt_contracts.odps.parser

::: dbt_contracts.odcs.parser

::: dbt_contracts.odcs.validator

::: dbt_contracts.generators.orchestrator

::: dbt_contracts.generators.exporter

::: dbt_contracts.generators.postprocess
