# dbt-contracts

Contract-driven dbt project generation powered by open standards.

Define your data products and contracts using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) and [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/), and `dbt-contracts` generates your dbt models, sources, staging SQL, and tests automatically.

## Why?

Most dbt projects start with manually written YAML and SQL that drifts from the actual data contracts over time. `dbt-contracts` flips this: **contracts are the source of truth**, and dbt artifacts are derived from them.

- **Single source of truth** — data product definitions and contracts drive everything
- **Drift detection** — see exactly what changed between your contracts and existing dbt artifacts before applying updates
- **Standards-based** — built on ODPS v1.0.0 and ODCS v3.1.0, not a proprietary format
- **Incremental adoption** — works alongside existing dbt projects; generate what you need, keep what you have

## Quick start

### Install

```sh
uv tool install dbt-contracts
```

### Initialize a project

```sh
dbt-contracts init --adapter duckdb
```

This scaffolds a complete dbt project with config file, directories, and connection profile.

### Add contracts

Place your ODPS product files in `contracts/products/` and ODCS contract files in `contracts/schemas/`.

### Generate dbt artifacts

```sh
# Generate with drift detection (prompts for changed files)
dbt-contracts generate

# Auto-accept all changes
dbt-contracts generate --yolo-mode

# Preview changes without writing
dbt-contracts generate --dry-run
```

### Validate contracts

```sh
dbt-contracts validate
```

## How it works

```
ODPS Data Product         ODCS Contracts
 (data product def)        (schema + rules)
        │                        │
        └──────┬─────────────────┘
               ▼
         dbt-contracts
               │
     ┌─────────┼──────────┐
     ▼         ▼          ▼
 sources.yml  schema.yml  stg_*.sql
```

Each ODPS product defines input and output ports referencing ODCS contracts by `contractId`. The tool resolves these references, exports dbt artifacts via `datacontract-cli`, and post-processes the output to wire up `source()` references using the product's lineage information.

## Documentation

Full documentation is available in the [`docs/`](docs/) directory:

- [CLI Reference](docs/cli.md) — all commands, flags, and interactive mode
- [Configuration](docs/configuration.md) — config file format and resolution order
- [Contracts](docs/contracts.md) — ODPS and ODCS contract formats
- [Architecture](docs/architecture.md) — how the generation pipeline works
- [API Reference](docs/api/index.md) — Python API for programmatic use
- [Troubleshooting](docs/troubleshooting.md) — common issues and solutions

## Development

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [just](https://github.com/casey/just?tab=readme-ov-file#installation)

### Setup

```sh
git clone <repo-url>
cd dbt-with-contracts
just install
```

### Common commands

| Command | Purpose |
|---------|---------|
| `just test` | Run pytest |
| `just check` | Run all checks (ruff, ruff-format, ty) |
| `just docs` | Build documentation |
| `just clean` | Remove caches and virtualenv |
