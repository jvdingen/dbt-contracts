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

### ODPS Parsing (available now)

```python
from pathlib import Path
from dbt_contracts.odps.parser import load_odps, get_input_ports, get_output_ports

product = load_odps(Path("my_product.odps.yaml"))

for port in get_input_ports(product):
    print(f"Input: {port.name} -> contract {port.contractId}")

for port in get_output_ports(product):
    print(f"Output: {port.name} -> contract {port.contractId}")
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
├── odcs/                   # ODCS v3.1.0 integration (planned)
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
