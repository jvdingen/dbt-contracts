# dbt-contracts

Contract-driven dbt workflow tool using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) and [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) to generate dbt models, sources, and tests.

## What it does

- **Input ports** in your ODPS product definitions become **dbt sources**
- **Output ports** become **dbt models** with column definitions and tests
- **Staging SQL** is auto-generated with `{{ source() }}` refs wired from `inputContracts` lineage

## Installation

```sh
uv tool install dbt-contracts
```

Or with pipx:

```sh
pipx install dbt-contracts
```

!!! tip "Python 3.14+"
    If your default Python is 3.14+, specify an earlier version:

    ```sh
    uv tool install --python python3.12 dbt-contracts
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

Prompts for a database adapter, then scaffolds a complete dbt project:

- `dbt-contracts.toml` -- configuration file
- `dbt_project.yml` -- dbt project config
- `profiles.yml` -- dbt connection profile
- `contracts/products/` -- ODPS product definitions
- `contracts/schemas/` -- ODCS contract files
- `models/`, `sources/`, `macros/`, `seeds/`, `tests/`, `analyses/`, `snapshots/`

### 2. Add your contract files

Place ODPS product definitions in `contracts/products/` and ODCS contracts in `contracts/schemas/`. See the [contracts guide](contracts.md) for file format details and examples.

### 3. Generate dbt artifacts

```sh
dbt-contracts generate
```

Produces:

```
sources/
└── sources.yml
models/
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

<div class="grid cards" markdown>

- :lucide-file-text: **[Contracts guide](contracts.md)**

    ODPS and ODCS file formats with full examples

- :lucide-terminal: **[CLI reference](cli.md)**

    All commands, options, and interactive mode

- :lucide-settings: **[Configuration](configuration.md)**

    Config file format, resolution order, and all settings

- :lucide-boxes: **[Architecture](architecture.md)**

    How the generation pipeline works under the hood

- :lucide-alert-triangle: **[Troubleshooting](troubleshooting.md)**

    Common errors and fixes

- :lucide-code: **[API reference](api/)**

    Python module documentation

</div>
