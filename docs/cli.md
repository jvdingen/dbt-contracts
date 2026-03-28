# CLI Reference

dbt-contracts provides commands for the full contract-to-dbt lifecycle. Also available as `dbtc`.

```bash
dbt-contracts --version  # Show version
dbt-contracts --help     # Show help
```

## Setup

### `init`

Initialize a `contracts/` directory with default configuration and subdirectories.

Creates:
- `contracts/config.yaml` --- Commented config template
- `contracts/contracts/` --- For ODCS contract files
- `contracts/products/` --- For ODPS product files

If `dbt_project.yml` is detected in the target directory, the config is set up accordingly.

```bash
dbt-contracts init [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--dir` | `.` | Directory where `contracts/` will be created |
| `--force` | `false` | Overwrite existing `contracts/` directory |

| Exit code | Meaning |
|---|---|
| 0 | Initialization succeeded |
| 1 | `contracts/` already exists (use `--force` to overwrite) |

## Validation

### `validate`

Validate all ODCS contracts and ODPS product definitions in the `contracts/` directory.

Runs three validation passes:

1. **Schema validation** --- Each ODCS contract is validated against the ODCS v3.1.0 JSON schema (via datacontract-cli)
2. **Cross-reference validation** --- All `contractId` fields in ODPS products are checked against discovered ODCS contract IDs (controlled by `validation.cross_reference` in config)
3. **Status checks** --- Contract statuses are checked against `validation.min_status` from config (default: `draft`)

```bash
dbt-contracts validate [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |

| Exit code | Meaning |
|---|---|
| 0 | All contracts and products are valid |
| 1 | Validation failed or contracts directory not found |

## Generation

### `generate`

Generate dbt models, sources, and SQL from validated contracts.

Runs validation first (unless `--skip-validation` is set), then generates:

- **Source YAML** --- One `sources.yml` per upstream source in `sources_dir`
- **Model YAML** --- One `schema.yml` per model in `models_dir`
- **Staging SQL** --- One `.sql` per model with `{{ source() }}` or `{{ ref() }}` references

Files include a header comment marking them as managed. On subsequent runs, managed files are overwritten while user-modified files are skipped (unless `--force`).

```bash
dbt-contracts generate [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config `generation.models_dir` | Override models output directory |
| `--sources-dir` | From config `generation.sources_dir` | Override sources output directory |
| `--force` | `false` | Overwrite non-managed files |
| `--dry-run` | `false` | Preview generated files without writing to disk |
| `--skip-validation` | `false` | Skip validation before generating |

| Exit code | Meaning |
|---|---|
| 0 | Generation succeeded |
| 1 | Validation failed or contracts directory not found |

## Drift detection

### `diff`

Show drift between contracts and the current dbt project state. Generates expected output in memory and compares with on-disk files.

```bash
dbt-contracts diff [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config | Override models output directory |
| `--sources-dir` | From config | Override sources output directory |
| `--format` | `text` | Output format: `text` or `json` |

| Exit code | Meaning |
|---|---|
| 0 | No drift detected |
| 1 | Drift detected (new or modified files) |

Use `--format json` in CI pipelines to machine-parse the output.

### `sync`

Sync the dbt project with contracts by applying any detected drift. Shows a preview of changes before applying.

```bash
dbt-contracts sync [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config | Override models output directory |
| `--sources-dir` | From config | Override sources output directory |
| `--yes` | `false` | Apply changes without confirmation |

## Import

### `import`

Generate ODCS contract stubs from existing dbt schema YAML files. Parses sources and models, creating draft contracts with column definitions and constraints.

```bash
dbt-contracts import SCHEMA_FILES... [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--output-dir` | `contracts/contracts` | Directory for generated contract files |
| `--server-type` | `snowflake` | Default server type for contracts |
| `--dry-run` | `false` | Preview without writing files |

## Utility

### `version`

Show the installed version.

```bash
dbt-contracts version
```
