# dbt-contracts

Contract-driven dbt workflow tool using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) and [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) to generate dbt models, sources, and tests.

## What it does

- **Input ports** in your ODPS product definitions become **dbt sources**
- **Output ports** become **dbt models** with column definitions and tests
- **Staging SQL** is auto-generated with `{{ source() }}` refs wired from `inputContracts` lineage

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

Creates:

- `dbt-contracts.toml` -- configuration file
- `contracts/products/` -- ODPS product definitions
- `contracts/schemas/` -- ODCS contract files
- `output/` -- generated dbt artifacts

### 2. Add your contract files

Place ODPS product definitions in `contracts/products/` and ODCS contracts in `contracts/schemas/`. See the [contracts guide](contracts.md) for file format details and examples.

### 3. Generate dbt artifacts

```sh
dbt-contracts generate
```

Produces:

```
output/
├── sources.yml
└── models/
    ├── schema.yml
    └── staging/
        └── stg_customer_summary.sql
```

### 4. Validate contracts

```sh
dbt-contracts validate
```

Lints all `.odcs.yaml` files for structural correctness (offline, no database needed).

## Next steps

- [Contracts guide](contracts.md) -- ODPS and ODCS file formats with full examples
- [CLI reference](cli.md) -- all commands, options, and interactive mode
- [Configuration](configuration.md) -- config file format, resolution order, and all settings
- [Architecture](architecture.md) -- how the generation pipeline works under the hood
- [Troubleshooting](troubleshooting.md) -- common errors and fixes
- [API reference](api.md) -- Python module documentation
