# dbt-contracts

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Generate and manage dbt projects through Bitol ODCS/ODPS data contracts.**

dbt-contracts brings contract-first development to the dbt ecosystem. Define your data contracts using the [Open Data Contract Standard (ODCS)](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) and data products using the [Open Data Product Standard (ODPS)](https://bitol-io.github.io/open-data-product-standard/v1.0.0/), then generate fully-configured dbt projects from them.

## Quick start

```bash
# Install
pip install dbt-contracts

# Initialize contracts in your dbt project
dbt-contracts init

# Validate contracts
dbt-contracts validate

# Generate dbt models
dbt-contracts generate
```

## Documentation

Full documentation is available at [jvdingen.github.io/dbt-contracts](https://jvdingen.github.io/dbt-contracts/).

## Development

```bash
# Clone and install
git clone https://github.com/jvdingen/dbt-contracts.git
cd dbt-contracts
just install

# Run tests
just test

# Run linter
just lint

# Build docs
just docs

# See all commands
just
```

## License

MIT
