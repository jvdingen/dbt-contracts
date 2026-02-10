# dbt-contracts

Contract-driven dbt workflow tool that uses [ODPS (Open Data Product Standard)](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) v1.0.0 and [ODCS (Open Data Contract Standard)](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) v3.1.0 to generate dbt models, sources, and tests.

## How It Works

ODPS files define **data products** with input and output ports. Each port references an ODCS contract via `contractId`. This tool parses the ODPS product definition, resolves the referenced contracts, and generates dbt artifacts.

```
ODPS Data Product ──> ODPS Parser ──> Resolve contractId refs
                                          │
                                          ▼
                                    ODCS Contracts
                                          │
                                          ▼
                                    dbt Artifacts
                                    ├── models/*.sql
                                    ├── schema.yml
                                    └── sources.yml
```

## Current Status

The project is under active development. Currently implemented:

- **ODPS parsing** — Pydantic models for ODPS v1.0.0 (`DataProduct`, `InputPort`, `OutputPort`, `Description`) and YAML file loading
- **ODCS integration** — Loading ODCS contracts via `open-data-contract-standard`, resolving contracts by `contractId`, and validation (lint + test) via `datacontract-cli`
- **Project scaffolding** — Package structure with `odps/`, `odcs/`, `generators/`, and `commands/` modules

See `docs/implementation-plan.md` for the full roadmap.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- [just](https://github.com/casey/just?tab=readme-ov-file#installation) — command runner

## Getting Started

```sh
git clone <repo-url>
cd dbt-with-contracts
just install
```

### Verify the setup

```sh
just check   # ruff, ruff-format, ty type checking
just test    # pytest
```

### Optional: Logfire observability

Copy `.env.example` to `.env` and set `LOGFIRE_TOKEN`. Without a token, logs go to the console only.

## Usage

### ODPS Parsing

```python
from pathlib import Path
from dbt_contracts.odps.parser import load_odps, get_input_ports, get_output_ports

product = load_odps(Path("my_product.odps.yaml"))

for port in get_input_ports(product):
    print(f"Input: {port.name} -> contract {port.contractId}")

for port in get_output_ports(product):
    print(f"Output: {port.name} -> contract {port.contractId}")
```

### ODCS Loading & Resolution

```python
from pathlib import Path
from dbt_contracts.odcs.parser import load_odcs, load_odcs_by_id

# Load a specific ODCS file
contract = load_odcs(Path("my_contract.odcs.yaml"))
print(f"{contract.name} (v{contract.version})")

# Resolve a contract by id (searches directory recursively)
contract = load_odcs_by_id("dbb7b1eb-7628-436e-8914-2a00638ba6db", Path("contracts/"))
```

### Contract Validation

```python
from pathlib import Path
from dbt_contracts.odcs.validator import lint_contract, test_contract

# Offline lint (no database needed)
passed, errors = lint_contract(Path("my_contract.odcs.yaml"))
if not passed:
    for error in errors:
        print(f"  {error}")

# Live test (requires server configuration)
passed, errors = test_contract(Path("my_contract.odcs.yaml"))
```

## Project Structure

```
src/dbt_contracts/
├── __init__.py
├── cli.py                  # CLI entry point
├── main.py                 # Greeting helpers
├── odps/                   # ODPS v1.0.0 parsing (implemented)
│   ├── schema.py           #   Pydantic models
│   └── parser.py           #   YAML loading + port helpers
├── odcs/                   # ODCS v3.1.0 integration (implemented)
│   ├── parser.py           #   Load contracts, resolve by contractId
│   └── validator.py        #   Lint + test via datacontract-cli
├── generators/             # dbt artifact generation (planned)
└── commands/               # CLI command implementations (planned)
```

## Development

| Command | Purpose |
|---------|---------|
| `just install` | Sync dependencies + install pre-commit hooks |
| `just test` | Run pytest |
| `just check` | Run all pre-commit hooks (ruff, ruff-format, ty) |
| `just lint` | Run ruff only |
| `just typing` | Run ty type checker only |
| `just docs` | Build documentation with zensical |
| `just clean` | Remove `.venv`, caches, `__pycache__` |
| `just update` | Upgrade lock file |
