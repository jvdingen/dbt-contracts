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

## Project Structure

```
dbt-contracts/
├── src/
│   └── dbt_contracts/
│       ├── __init__.py           # Package version
│       ├── cli/
│       │   └── __init__.py       # Click group (version, validate commands)
│       ├── core/                 # Core logic (generation, validation)
│       │   ├── __init__.py
│       │   ├── adapter.py        # Adapter wrapping datacontract-cli exporters
│       │   ├── discovery.py      # Contract/product file scanning
│       │   └── validation.py     # ODCS lint, cross-ref, status checks
│       ├── models/               # Pydantic models (config, ODPS)
│       │   └── __init__.py
│       └── templates/            # Jinja2 templates for dbt artifacts
├── tests/
│   ├── fixtures/                 # ODCS/ODPS test fixtures
│   │   ├── *.odcs.yaml           # Individual contract fixtures
│   │   ├── *.odps.yaml           # Individual product fixtures
│   │   └── sample_project/       # Full project structure fixture
│   ├── conftest.py
│   ├── test_adapter.py           # Adapter layer tests
│   ├── test_cli.py               # CLI smoke tests
│   ├── test_cli_validate.py      # Validate command tests
│   ├── test_discovery.py         # Discovery module tests
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

## Development Phases

### Phase 0: Project Scaffolding ✅
**Goal**: Reviewable project skeleton with all tooling configured.

1. **pyproject.toml** — Package metadata, dependencies, entry points, ruff/pytest config
2. **justfile** — Commands: install, test, lint, format, docs, docs-serve, build, clean
3. **zensical.toml** — Documentation site configuration
4. **Source skeleton** — `src/dbt_contracts/` with `__init__.py`, cli/, core/, models/, templates/
5. **CLI entry point** — Click group with `version` command, dual entry points (`dbt-contracts` + `dbtc`)
6. **Test skeleton** — conftest.py + basic CLI smoke test
7. **Documentation skeleton** — All docs/ pages with initial content
8. **README.md** — Project overview with badges and quickstart

### Phase 1: Core Models ✅
**Goal**: Config model and hand-rolled ODPS Pydantic models.

1. **Core config model** — Pydantic model for `contracts/config.yaml` (project settings, mappings)
2. **ODPS model** — Pydantic model for ODPS v1.0.0 (hand-rolled from spec, matching ODCS SDK methodology)
3. **Tests** — Unit tests for config and ODPS model loading/validation
4. **Docs** — Update configuration.md and products.md

### Phase 2: Adapter Layer ✅
**Goal**: Thin adapter wrapping datacontract-cli for linting and lineage-aware dbt rendering.

1. **datacontract-cli dependency** — Added as library for dbt export and ODCS validation
2. **Adapter module** (`core/adapter.py`) — `lint()` validates ODCS via datacontract-cli; `render()` takes contracts + products, classifies via ODPS lineage, returns parsed dicts
3. **Lineage classification** — ODPS `outputPorts` → models, `inputPorts` → sources, `inputPorts` that are also `outputPorts` of another ODPS → refs
4. **Staging SQL** — References upstream contracts via `source()` or `ref()` based on lineage
5. **Result models** — `LintResult`, `GenerationResult` Pydantic models
6. **Tests** — 16 tests against real datacontract-cli with ODCS/ODPS fixtures

### Phase 3: Contract Discovery ✅
**Goal**: Scan `/contracts` directory, parse and load all ODCS and ODPS files.

1. **Discovery module** (`core/discovery.py`) — Scan `contracts/*.odcs.yaml` and `products/*.odps.yaml`
2. **Config loading** — Load `config.yaml` from contracts directory, fall back to defaults
3. **Tests** — Discovery with valid/invalid directory structures

### Phase 4: Validation ✅
**Goal**: Validate contracts and cross-references, expose via CLI.

1. **Validation module** (`core/validation.py`) — ODCS lint via adapter, cross-reference checks (gated by `config.validation.cross_reference`), status threshold checks (against `config.validation.min_status`)
2. **`validate` CLI command** — Runs discovery + validation, structured error output, exit code 1 on failure
3. **Tests** — Valid/invalid contracts, broken cross-refs, status thresholds, cross-ref disabled

### Phase 5: dbt Generation
**Goal**: Full generation of model YAMLs, source YAMLs, and SQL from contracts.

1. **Post-processor** (`core/postprocess.py`) — Inject headers, ODPS metadata, strip tests per config, SLA/custom metadata mapping
2. **SQL enhancer** (`core/sql_enhancer.py`) — Casting, renaming on top of adapter staging SQL (using `sqlglot`)
3. **Generator orchestrator** (`core/generator.py`) — Discovery → render via adapter → post-process → write files, overwrite protection
4. **`generate` CLI command** — `--contracts-dir`, `--output-dir`, `--force`, `--dry-run`, `--server-type`, `--contract`
5. **Tests** — Snapshot tests comparing generated output to expected dbt artifacts

### Phase 6: Init & Bootstrap
**Goal**: Project scaffolding for new and existing dbt projects.

1. **`init` command** — Create `/contracts` structure, default config, detect existing `dbt_project.yml`
2. **`bootstrap` command** — Init + sample contracts + run generate
3. **Tests** — End-to-end: init → add contracts → generate → valid dbt project

### Phase 7: Diff, Sync & Import
**Goal**: Keep dbt project in sync with contracts over time.

1. **Diff engine** (`core/differ.py`) — Generate expected in memory, compare with on-disk
2. **`diff` command** — Human-readable or JSON output, exit code 1 on drift
3. **`sync` command** — Apply diff changes, interactive confirmation or `--yes`
4. **`import` command** — Parse existing dbt YAML, generate ODCS contract stubs
5. **CI integration** — `--format json` for all commands, documented exit codes

## Commands

| Command | Description | Phase |
|---|---|---|
| `dbt-contracts version` | Show version | 0 ✅ |
| `dbt-contracts validate` | Validate all contracts and products | 4 |
| `dbt-contracts generate` | Generate dbt models from contracts | 5 |
| `dbt-contracts init` | Initialize `/contracts` directory | 6 |
| `dbt-contracts bootstrap` | Create full dbt project from contracts | 6 |
| `dbt-contracts diff` | Show drift between contracts and dbt | 7 |
| `dbt-contracts sync` | Sync dbt project with contracts | 7 |
| `dbt-contracts import` | Generate contracts from existing dbt | 7 |

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
