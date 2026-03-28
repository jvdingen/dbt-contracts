# dbt-contracts

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Contract-first dbt development using open standards.**

dbt-contracts generates and manages dbt projects from data contracts. You define *what* your data looks like using [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) (Open Data Contract Standard), how data flows between products using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) (Open Data Product Standard), and dbt-contracts produces the dbt models, source definitions, staging SQL, and tests for you.

## Why contract-first?

Traditional dbt development starts with SQL and adds documentation, tests, and schema definitions after the fact. Contract-first flips this:

1. **Define the contract** --- the shape of the data, quality rules, ownership, and SLAs
2. **Generate the dbt project** --- models, sources, staging SQL, and tests are produced automatically
3. **Keep it in sync** --- detect drift, sync changes, and import existing dbt projects back into contracts

This means producers and consumers agree on the data shape before anyone writes SQL, and the dbt project always reflects the contract.

## How it works

```
contracts/
  contracts/*.odcs.yaml    -->  models/schema.yml + stg_*.sql
  products/*.odps.yaml     -->  sources.yml (lineage-aware)
  config.yaml              -->  generation settings
```

ODPS products define lineage: `inputPorts` become dbt sources, `outputPorts` become dbt models. When an input port is also an output of another product, the staging SQL uses `{{ ref() }}` instead of `{{ source() }}`.

## Quick start

```bash
pip install dbt-contracts
```

**Starting from contracts:**

```bash
cd my-dbt-project
dbt-contracts init                  # scaffold contracts/ directory
# ... add your .odcs.yaml and .odps.yaml files ...
dbt-contracts validate              # check contracts are valid
dbt-contracts generate              # generate dbt artifacts
```

**Starting from an existing dbt project:**

```bash
dbt-contracts import models/schema.yml    # generate contract stubs
# ... refine contracts, add ODPS products ...
dbt-contracts generate                     # regenerate dbt from contracts
```

**Keeping things in sync:**

```bash
dbt-contracts diff                  # check for drift
dbt-contracts sync --yes            # apply changes
```

## Commands

| Command | Description |
|---|---|
| `init` | Scaffold a `contracts/` directory with default config |
| `validate` | Validate contracts (schema, cross-references, status) |
| `generate` | Generate dbt models, sources, and SQL from contracts |
| `diff` | Show drift between contracts and dbt project |
| `sync` | Apply drift to bring dbt project in line with contracts |
| `import` | Generate ODCS contract stubs from existing dbt YAML |

See the [CLI reference](https://jvdingen.github.io/dbt-contracts/cli/) for full options and flags.

## Built on open standards

dbt-contracts is built on two [Bitol](https://bitol.io/) standards (Linux Foundation AI & Data):

- **[ODCS v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)** --- Define data contracts: schema, quality rules, SLAs, ownership
- **[ODPS v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)** --- Define data products: input/output ports, lineage, governance

It uses the official [`open-data-contract-standard`](https://pypi.org/project/open-data-contract-standard/) Python SDK and [`datacontract-cli`](https://github.com/datacontract/datacontract-cli) for contract parsing, validation, and dbt export.

## Documentation

Full documentation: [jvdingen.github.io/dbt-contracts](https://jvdingen.github.io/dbt-contracts/)

- [Getting Started](https://jvdingen.github.io/dbt-contracts/getting-started/) --- Installation and first contract
- [Contracts Guide](https://jvdingen.github.io/dbt-contracts/contracts/) --- Writing ODCS contracts
- [Products Guide](https://jvdingen.github.io/dbt-contracts/products/) --- Writing ODPS data products
- [Configuration](https://jvdingen.github.io/dbt-contracts/configuration/) --- Config file reference
- [Architecture](https://jvdingen.github.io/dbt-contracts/architecture/) --- How it works under the hood

## Development

```bash
git clone https://github.com/jvdingen/dbt-contracts.git
cd dbt-contracts
just install    # install in dev mode
just check      # lint + test
just docs       # build documentation
```

## License

MIT
