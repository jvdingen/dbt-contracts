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

- **ODPS parsing** — Pydantic models for ODPS v1.0.0 (`DataProduct`, `InputPort`, `OutputPort`, `InputContract`) and YAML file loading
- **ODCS integration** — Loading ODCS contracts via `open-data-contract-standard`, resolving contracts by `contractId`, and validation (lint + test) via `datacontract-cli`
- **dbt generation pipeline** — Export dbt sources, models, and staging SQL from ODCS contracts via `datacontract-cli`; post-process to rename sources, merge files, and rewrite `source()` refs using ODPS `inputContracts` lineage; orchestrate end-to-end generation from an ODPS data product definition
- **CLI & configuration** — Click-based CLI with `init`, `generate`, and `validate` subcommands; interactive menu mode via questionary; TOML configuration file support (`dbt-contracts.toml` or `[tool.dbt-contracts]` in `pyproject.toml`)

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

### CLI

```sh
# Initialize a new project (creates config file + directories)
dbt-contracts init

# Generate dbt artifacts from all ODPS products
dbt-contracts generate

# Generate from a specific product, dry-run mode
dbt-contracts generate --product my_product.odps.yaml --dry-run

# Validate all ODCS contracts (lint by default)
dbt-contracts validate

# Validate with live data testing
dbt-contracts validate --live

# Validate a specific contract
dbt-contracts validate --contract my_contract.odcs.yaml

# Use a custom config file
dbt-contracts --config path/to/config.toml generate

# Interactive mode (default when no subcommand given)
dbt-contracts
```

### Configuration

Configuration is loaded from (in order of precedence):

1. Explicit `--config` path
2. `dbt-contracts.toml` in the project root
3. `[tool.dbt-contracts]` section in `pyproject.toml`
4. Defaults (no config file needed)

```toml
# dbt-contracts.toml
cli_mode = "interactive"  # "interactive" or "subcommand"

[paths]
odps_dir = "contracts/products"
odcs_dir = "contracts/schemas"
output_dir = "output"

[generation]
overwrite_existing = false
dry_run = false

[validation]
default_mode = "lint"  # "lint" or "test"
fail_on_error = false
```

### Python API

#### ODPS Parsing

```python
from pathlib import Path
from dbt_contracts.odps.parser import load_odps, get_input_ports, get_output_ports

product = load_odps(Path("my_product.odps.yaml"))

for port in get_input_ports(product):
    print(f"Input: {port.name} -> contract {port.contractId}")

for port in get_output_ports(product):
    print(f"Output: {port.name} -> contract {port.contractId}")
```

#### ODCS Loading & Resolution

```python
from pathlib import Path
from dbt_contracts.odcs.parser import load_odcs, load_odcs_by_id

# Load a specific ODCS file
contract = load_odcs(Path("my_contract.odcs.yaml"))
print(f"{contract.name} (v{contract.version})")

# Resolve a contract by id (searches directory recursively)
contract = load_odcs_by_id("dbb7b1eb-7628-436e-8914-2a00638ba6db", Path("contracts/"))
```

#### Contract Validation

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

#### dbt Generation

```python
from pathlib import Path
from dbt_contracts.generators.orchestrator import generate_for_product

# Generate dbt artifacts from an ODPS data product
files = generate_for_product(
    product_path=Path("my_product.odps.yaml"),
    odcs_dir=Path("contracts/"),
    output_dir=Path("dbt_output/"),
)

for f in files:
    print(f"Generated: {f}")
# Generated: dbt_output/sources.yml
# Generated: dbt_output/models/schema.yml
# Generated: dbt_output/models/staging/stg_customer_summary.sql
```

The pipeline resolves each port's `contractId`, exports dbt artifacts via `datacontract-cli`, and uses the `inputContracts` lineage on output ports to rewrite `source()` refs so staging SQL points to the correct input port sources.

You can also use the lower-level functions directly:

```python
from dbt_contracts.odcs.parser import load_odcs
from dbt_contracts.generators.exporter import export_model_schema, export_sources, export_staging_sql
from dbt_contracts.generators.postprocess import rename_source, rewrite_source_refs

contract = load_odcs(Path("my_contract.odcs.yaml"))

# Export individual artifacts
sources_yaml = export_sources(contract)       # sources.yml (source name = contract UUID)
schema_yaml = export_model_schema(contract)   # schema.yml (models + columns + constraints)
staging_sql = export_staging_sql(contract)    # staging SQL with source() ref

# Post-process
sources_yaml = rename_source(sources_yaml, contract.id, "my_port_name")
staging_sql = rewrite_source_refs(staging_sql, contract.id, "my_port_name")
```

## Project Structure

```
src/dbt_contracts/
├── __init__.py
├── cli.py                  # Click CLI entry point (init, generate, validate)
├── config.py               # Pydantic config models + TOML loading
├── interactive.py          # Interactive menu mode (questionary)
├── odps/                   # ODPS v1.0.0 parsing
│   ├── schema.py           #   Pydantic models (DataProduct, InputPort, OutputPort, InputContract)
│   └── parser.py           #   YAML loading + port helpers
├── odcs/                   # ODCS v3.1.0 integration
│   ├── parser.py           #   Load contracts, resolve by contractId
│   └── validator.py        #   Lint + test via datacontract-cli
├── generators/             # dbt artifact generation
│   ├── exporter.py         #   Thin wrappers around datacontract-cli export
│   ├── postprocess.py      #   Rename sources, merge files, rewrite source() refs
│   └── orchestrator.py     #   End-to-end generation from ODPS product
└── commands/               # CLI command implementations
    ├── init.py             #   Scaffold project structure
    ├── generate.py         #   Generate dbt artifacts
    └── validate.py         #   Validate ODCS contracts
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
