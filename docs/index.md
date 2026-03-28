# dbt-contracts

**Generate and manage dbt projects through Bitol ODCS/ODPS data contracts.**

dbt-contracts brings contract-first development to the dbt ecosystem. Define your data contracts using the [Open Data Contract Standard (ODCS)](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) and data products using the [Open Data Product Standard (ODPS)](https://bitol-io.github.io/open-data-product-standard/v1.0.0/), then generate fully-configured dbt projects from them.

## Why contract-first?

Traditional dbt development starts with models and adds documentation and tests after the fact. Contract-first development flips this: you define the contract — the shape of the data, its quality rules, ownership, and SLAs — before writing any SQL. This means:

- **Alignment before code** — Producers and consumers agree on the data shape upfront.
- **Automated scaffolding** — dbt models, schema files, and tests are generated from contracts.
- **Drift detection** — Ensure your dbt project stays in sync with its contracts over time.
- **Standards-based** — Built on open standards (ODCS, ODPS) backed by the Linux Foundation.

## Quick start

```bash
# Install
pip install dbt-contracts

# Initialize contracts in an existing dbt project
dbt-contracts init

# Validate your contracts
dbt-contracts validate

# Generate dbt models from contracts
dbt-contracts generate
```

## Features

| Feature | Description |
|---|---|
| **Contract validation** | Parse and validate ODCS contracts and ODPS product definitions |
| **dbt generation** | Generate models, schema.yml, sources, and staging SQL from contracts |
| **Quality mapping** | Automatically map ODCS quality checks to dbt tests |
| **Project init** | Scaffold a `contracts/` directory in any dbt project |
| **Drift detection** | Compare dbt models against their contracts with `diff` |
| **Sync & import** | Sync contracts to dbt, or import existing dbt schemas as contracts |

## Next steps

- [Getting Started](getting-started.md) — Installation and first steps
- [CLI Reference](cli.md) — All available commands
- [Contracts Guide](contracts.md) — Writing ODCS contracts
- [Products Guide](products.md) — Writing ODPS data products
- [Configuration](configuration.md) — Configuring dbt-contracts
- [Architecture](architecture.md) — How it works under the hood
