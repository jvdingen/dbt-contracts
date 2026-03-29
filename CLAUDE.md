# dbt-contracts

A CLI tool that uses the [Bitol ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) (Open Data Contract Standard) and [Bitol ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) (Open Data Product Standard) to generate and manage dbt projects through data contracts.

## Project Vision

- **Contract-first dbt development**: Define data contracts (ODCS) and data products (ODPS), then generate dbt models, schemas, and tests from them.
- **CLI-driven workflow**: Provide CLI commands for initializing, generating, validating, diffing, syncing, and importing contracts.
- **`/contracts` convention**: Every dbt project managed by this tool has a `/contracts` directory containing CLI config, ODCS contract YAML files, and ODPS product YAML files.
- **Powered by the official SDK**: Uses [`open-data-contract-standard`](https://pypi.org/project/open-data-contract-standard/) Python SDK (Pydantic v2 models) for parsing, validating, and generating ODCS contracts.

## Standards Reference

### ODCS (Open Data Contract Standard) v3.1.0
- **Kind**: `DataContract`, **apiVersion**: `v3.1.0`
- Top-level: `id`, `version`, `status`, `name`, `domain`, `dataProduct`, `servers`, `schema`, `team`, `slaProperties`, `support`, `price`, `roles`, `customProperties`
- Schema contains `SchemaObject` (tables) with `SchemaProperty` (columns) supporting `logicalType`, `physicalType`, `quality` checks, `relationships`, etc.
- Statuses: `proposed` → `draft` → `active` → `deprecated` → `retired`
- JSON Schema: https://github.com/bitol-io/open-data-contract-standard/blob/main/schema/odcs-json-schema-v3.1.0.json

### ODPS (Open Data Product Standard) v1.0.0
- **Kind**: `DataProduct`, **apiVersion**: `v1.0.0`
- Top-level: `id`, `version`, `status`, `name`, `domain`, `inputPorts`, `outputPorts`, `managementPorts`, `team`, `support`, `customProperties`
- Ports pattern: `inputPorts` (data sources), `outputPorts` (exposed data with `contractId` linking to ODCS), `managementPorts` (observability/control)
- Same lifecycle statuses as ODCS

### Python SDK (`open-data-contract-standard` v3.1.2+)
- Install: `pip install open-data-contract-standard`
- Main class: `OpenDataContractStandard` from `open_data_contract_standard.model`
- Key methods: `from_file()`, `from_string()`, `to_yaml()`, `json_schema()`
- Note: `schema` field aliased as `schema_` in Python, `from` as `from_` in Relationship

## Tech Stack

- **Language**: Python >= 3.10
- **CLI framework**: click
- **dbt generation**: datacontract-cli (used as a library for dbt export + linting)
- **Data models**: Pydantic v2 (via SDK + custom ODPS models)
- **Package manager**: uv
- **Task runner**: just
- **Testing**: pytest
- **Linting/Formatting**: ruff
- **Documentation**: Zensical (zensical.toml config, docs/ directory)

## CLI Entry Points

The tool registers two CLI entry points:
- `dbt-contracts` — full name
- `dbtc` — shorthand

Both invoke the same click group.

## Commands

| Command | Description |
|---|---|
| `dbt-contracts version` | Show version |
| `dbt-contracts validate` | Validate all contracts and products |
| `dbt-contracts generate` | Generate dbt models, sources, and SQL from contracts |
| `dbt-contracts init` | Initialize `/contracts` directory |
| `dbt-contracts diff` | Show drift between contracts and dbt project |
| `dbt-contracts sync` | Sync dbt project with contracts |
| `dbt-contracts import` | Generate ODCS contracts from existing dbt schema YAML |

## Project Structure

```
dbt-contracts/
├── src/
│   └── dbt_contracts/
│       ├── __init__.py           # Package version
│       ├── cli/
│       │   └── __init__.py       # Click group (all commands)
│       ├── core/
│       │   ├── __init__.py       # Public exports
│       │   ├── adapter.py        # Adapter wrapping datacontract-cli exporters
│       │   ├── differ.py         # Drift detection (diff engine)
│       │   ├── discovery.py      # Contract/product file scanning
│       │   ├── generator.py      # dbt artifact generation orchestrator
│       │   ├── importer.py       # dbt YAML → ODCS contract stubs
│       │   ├── init.py           # Project scaffolding
│       │   └── validation.py     # ODCS lint, cross-ref, status checks
│       ├── models/               # Pydantic models (config, ODPS)
│       │   └── __init__.py
│       └── templates/            # Jinja2 templates (reserved)
├── tests/
│   ├── fixtures/                 # ODCS/ODPS test fixtures
│   │   ├── *.odcs.yaml           # Individual contract fixtures
│   │   ├── *.odps.yaml           # Individual product fixtures
│   │   └── sample_project/       # Full project structure fixture
│   ├── conftest.py
│   ├── test_adapter.py           # Adapter layer tests
│   ├── test_cli.py               # CLI smoke tests
│   ├── test_cli_diff_sync_import.py  # Diff/sync/import command tests
│   ├── test_cli_generate.py      # Generate command tests
│   ├── test_cli_init.py          # Init command tests
│   ├── test_cli_validate.py      # Validate command tests
│   ├── test_config.py            # Config model tests
│   ├── test_differ.py            # Differ module tests
│   ├── test_discovery.py         # Discovery module tests
│   ├── test_generator.py         # Generator module tests
│   ├── test_importer.py          # Importer module tests
│   ├── test_init.py              # Init module tests
│   ├── test_odps.py              # ODPS model tests
│   └── test_validation.py        # Validation logic tests
├── docs/
│   ├── index.md                  # Homepage
│   ├── getting-started.md        # Installation & quickstart
│   ├── cli.md                    # CLI command reference
│   ├── contracts.md              # ODCS contract guide
│   ├── products.md               # ODPS product guide
│   ├── configuration.md          # Config file reference
│   ├── architecture.md           # How it works
│   ├── troubleshooting.md        # Common issues
│   └── api/                      # API reference (mkdocstrings)
│       ├── index.md
│       ├── cli.md
│       ├── configuration.md
│       ├── contracts.md
│       └── generation.md
├── pyproject.toml
├── justfile
├── zensical.toml
├── LICENSE
├── README.md
├── CLAUDE.md
└── .claude/
    └── commands/
        ├── odcs.md               # /odcs agent skill
        └── odps.md               # /odps agent skill
```

## `/contracts` Directory Convention (in target dbt projects)

```
my-dbt-project/
├── contracts/
│   ├── config.yaml           # dbt-contracts CLI configuration
│   ├── contracts/            # ODCS contract YAML files
│   │   └── *.odcs.yaml
│   └── products/             # ODPS product YAML files
│       └── *.odps.yaml
├── models/                   # Generated dbt models
├── dbt_project.yml
└── ...
```

## Core Architecture

### Adapter Layer (`core/adapter.py`)
Thin adapter wrapping datacontract-cli for linting and lineage-aware dbt rendering:
- `lint()` validates ODCS contracts via datacontract-cli (serializes to YAML string first)
- `render()` takes contracts + products, classifies via ODPS lineage, returns parsed dicts
- Lineage: `outputPorts` → models, `inputPorts` → sources, `inputPorts` that are also `outputPorts` of another ODPS → refs
- Staging SQL uses `{{ source() }}` for pure sources, `{{ ref() }}` for intermediate models

### Discovery (`core/discovery.py`)
Scans `contracts/` directory, loads config (with fallback defaults), parses all ODCS and ODPS files.

### Validation (`core/validation.py`)
Three passes: ODCS lint, cross-reference validation (gated by config), status threshold checks.

### Generator (`core/generator.py`)
Orchestrates render → post-process → write: one `.yml` + one `.sql` per model, sources in separate dir. Overwrite protection via header detection, `--force` override, `--dry-run` support.

### Differ (`core/differ.py`)
Generates expected output in memory (dry-run), compares with on-disk state. Reports new/modified/unchanged.

### Importer (`core/importer.py`)
Parses dbt schema YAML (sources and models), generates ODCS contract stubs with columns and constraints.

### Init (`core/init.py`)
Scaffolds `contracts/` directory with config template, detects `dbt_project.yml`.

## Future: Governance Integration (Phase 8)

Goal: keep local contract files in sync with contracts defined in external governance tooling (Atlan, Collibra, DataHub, OpenMetadata, etc.).

**Approach:** Start with a pull model where the governance tool is the source of truth.

- `dbt-contracts pull` fetches ODCS/ODPS definitions from a governance platform and writes them to `contracts/`
- `dbt-contracts push` publishes local contracts to a governance platform after validation
- Pluggable backend system so different governance tools can be supported via adapters
- Config extension: `governance.backend`, `governance.url`, `governance.project` etc.
- CI workflow: `pull` → `generate` → `diff` → block on drift

This phase is not yet started. The local-file workflow (define → validate → generate → diff → sync) is complete.

## just Commands

| Command | Description |
|---|---|
| `just install` | Install package in dev mode with all dependencies |
| `just test` | Run pytest |
| `just lint` | Run ruff check |
| `just format` | Run ruff format |
| `just check` | Run lint + test |
| `just docs` | Build documentation with Zensical |
| `just docs-serve` | Serve documentation locally with live reload |
| `just build` | Build distribution packages |
| `just clean` | Remove build artifacts and caches |

## Conventions

- Contract files use `.odcs.yaml` extension
- Product files use `.odps.yaml` extension
- Generated code includes a header comment indicating it was generated by dbt-contracts
- Never overwrite user-modified files without confirmation or `--force` flag
- All user-facing documentation lives in `docs/` and is built with Zensical
- Use `/odcs` and `/odps` agent skills for standard-specific questions during development
