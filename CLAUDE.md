# dbt-contracts

A CLI tool that uses the [Bitol ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) (Open Data Contract Standard) and [Bitol ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) (Open Data Product Standard) to generate and manage dbt projects through data contracts.

## Project Vision

- **Contract-first dbt development**: Define data contracts (ODCS) and data products (ODPS), then generate dbt models, schemas, and tests from them.
- **CLI-driven workflow**: Provide CLI commands for bootstrapping new dbt projects from contracts, and for managing contracts within existing dbt projects.
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

## Project Structure

```
dbt-contracts/
├── src/
│   └── dbt_contracts/
│       ├── __init__.py           # Package version
│       ├── cli/
│       │   ├── __init__.py       # Click group (main entry point)
│       │   └── version.py        # version command
│       ├── core/                 # Core logic (generation, validation)
│       │   └── __init__.py
│       ├── models/               # Pydantic models (config, ODPS)
│       │   └── __init__.py
│       └── templates/            # Jinja2 templates for dbt artifacts
├── tests/
│   ├── conftest.py
│   └── test_cli.py
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

## Development Phases

### Phase 0: Project Scaffolding (current)
**Goal**: Reviewable project skeleton with all tooling configured.

1. **pyproject.toml** — Package metadata, dependencies, entry points, ruff/pytest config
2. **justfile** — Commands: install, test, lint, format, docs, docs-serve, build, clean
3. **zensical.toml** — Documentation site configuration
4. **Source skeleton** — `src/dbt_contracts/` with `__init__.py`, cli/, core/, models/, templates/
5. **CLI entry point** — Click group with `version` command, dual entry points (`dbt-contracts` + `dbtc`)
6. **Test skeleton** — conftest.py + basic CLI smoke test
7. **Documentation skeleton** — All docs/ pages with initial content
8. **README.md** — Project overview with badges and quickstart

### Phase 1: Core Models
**Goal**: Config model and hand-rolled ODPS Pydantic models.

1. **Core config model** — Pydantic model for `contracts/config.yaml` (project settings, mappings)
2. **ODPS model** — Pydantic model for ODPS v1.0.0 (hand-rolled from spec, matching ODCS SDK methodology)
3. **Tests** — Unit tests for config and ODPS model loading/validation
4. **Docs** — Update configuration.md and products.md

### Phase 2: Contract Reading & Validation
**Goal**: Read ODCS contracts and ODPS products from `/contracts`, validate them.

1. **Contract discovery** — Scan `/contracts/contracts/*.odcs.yaml` and `/contracts/products/*.odps.yaml`
2. **Validation command** — `dbt-contracts validate`
3. **Cross-reference validation** — Check that ODPS `contractId` references resolve to actual ODCS files
4. **Error reporting** — Clear error messages with file paths and line numbers
5. **Tests** — Fixtures with valid/invalid contracts, validation edge cases
6. **Docs** — Update cli.md, contracts.md

### Phase 3: dbt Model Generation
**Goal**: Generate dbt SQL models and `schema.yml` from ODCS contracts.

1. **Schema-to-dbt mapping** — Map ODCS `SchemaObject`/`SchemaProperty` to dbt model YAML
2. **SQL generation** — Generate stub SQL models (SELECT with column list from contract)
3. **Server-to-source mapping** — Map ODCS `servers` to dbt `sources.yml`
4. **Generate command** — `dbt-contracts generate`
5. **Diff/update mode** — Detect existing models and show what would change
6. **Tests** — Snapshot tests comparing generated output to expected dbt artifacts
7. **Docs** — Update cli.md, architecture.md

### Phase 4: Quality & Testing Generation
**Goal**: Generate dbt tests from ODCS quality rules.

1. **Quality-to-test mapping** — Map ODCS `DataQuality` to dbt generic tests
2. **Custom test generation** — Generate custom tests for unmapped quality rules
3. **SLA metadata** — Embed SLA properties as dbt meta fields
4. **Tests** — Validate generated test YAML
5. **Docs** — Update contracts.md with quality mapping reference

### Phase 5: Bootstrap & Init Commands
**Goal**: Full project bootstrapping from scratch.

1. **Init command** — `dbt-contracts init`
2. **Bootstrap command** — `dbt-contracts bootstrap`
3. **Interactive mode** — Guided prompts for project name, warehouse type, etc.
4. **Tests** — End-to-end test: init → add contracts → generate → valid dbt project
5. **Docs** — Update getting-started.md, cli.md

### Phase 6: Sync & Drift Detection
**Goal**: Keep dbt project in sync with contracts over time.

1. **Drift detection** — `dbt-contracts diff`
2. **Sync command** — `dbt-contracts sync`
3. **Reverse sync** — `dbt-contracts import`
4. **CI integration** — Exit codes and machine-readable output
5. **Docs** — Update cli.md, add CI guide

## Commands

| Command | Description | Phase |
|---|---|---|
| `dbt-contracts version` | Show version | 0 |
| `dbt-contracts validate` | Validate all contracts and products | 2 |
| `dbt-contracts generate` | Generate dbt models from contracts | 3 |
| `dbt-contracts init` | Initialize `/contracts` directory | 5 |
| `dbt-contracts bootstrap` | Create full dbt project from contracts | 5 |
| `dbt-contracts diff` | Show drift between contracts and dbt | 6 |
| `dbt-contracts sync` | Sync dbt project with contracts | 6 |
| `dbt-contracts import` | Generate contracts from existing dbt | 6 |

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
