# CLI Reference

dbt-contracts provides a set of commands for managing data contracts and generating dbt projects. A shorthand `dbtc` alias is also available.

## Global options

```bash
dbt-contracts --version  # Show version
dbt-contracts --help     # Show help
```

## Commands

### `version`

Show the installed version of dbt-contracts.

```bash
dbt-contracts version
```

### `validate`

Validate all ODCS contracts and ODPS product definitions in the `contracts/` directory.

Runs three validation passes:

1. **Schema validation** — Each ODCS contract is validated against the ODCS v3.1.0 JSON schema (via datacontract-cli)
2. **Cross-reference validation** — All `contractId` fields in ODPS products are checked against discovered ODCS contract IDs (controlled by `validation.cross_reference` in config)
3. **Status checks** — Contract statuses are checked against `validation.min_status` from config (default: `draft`)

```bash
dbt-contracts validate [--contracts-dir PATH]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | All contracts and products are valid |
| 1 | Validation failed or contracts directory not found |

### `generate`

Generate dbt models, sources, and SQL from validated contracts.

Runs validation first (unless `--skip-validation` is set), then generates:

- **Source YAML** — One `sources.yml` per upstream source in `sources_dir`
- **Model YAML** — One `schema.yml` per model in `models_dir`
- **Staging SQL** — One `.sql` per model with `{{ source() }}` or `{{ ref() }}` references

Files include a header comment marking them as managed. On subsequent runs, managed files are overwritten while user-modified files are skipped (unless `--force`).

```bash
dbt-contracts generate [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config `generation.models_dir` | Override models output directory |
| `--sources-dir` | From config `generation.sources_dir` | Override sources output directory |
| `--force` | `false` | Overwrite non-managed files |
| `--dry-run` | `false` | Preview generated files without writing to disk |
| `--skip-validation` | `false` | Skip validation before generating |

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Generation succeeded |
| 1 | Validation failed or contracts directory not found |

### `init`

Initialize a `contracts/` directory with default configuration and subdirectories.

Creates:
- `contracts/config.yaml` — Commented config template
- `contracts/contracts/` — For ODCS contract files
- `contracts/products/` — For ODPS product files

If `dbt_project.yml` is detected in the target directory, the config is set up accordingly.

```bash
dbt-contracts init [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--dir` | `.` | Directory where `contracts/` will be created |
| `--force` | `false` | Overwrite existing `contracts/` directory |

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Initialization succeeded |
| 1 | `contracts/` already exists (use `--force` to overwrite) |

### `diff`

Show drift between contracts and the current dbt project state. Generates expected output in memory and compares with on-disk files.

```bash
dbt-contracts diff [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config | Override models output directory |
| `--sources-dir` | From config | Override sources output directory |
| `--format` | `text` | Output format: `text` or `json` |

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | No drift detected |
| 1 | Drift detected (new or modified files) |

### `sync`

Sync the dbt project with contracts by applying any detected drift. Shows a preview of changes before applying.

```bash
dbt-contracts sync [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--models-dir` | From config | Override models output directory |
| `--sources-dir` | From config | Override sources output directory |
| `--yes` | `false` | Apply changes without confirmation |

### `import`

Generate ODCS contract stubs from existing dbt schema YAML files. Parses sources and models, creating draft contracts with column definitions and constraints.

```bash
dbt-contracts import SCHEMA_FILES... [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--output-dir` | `contracts/contracts` | Directory for generated contract files |
| `--server-type` | `snowflake` | Default server type for contracts |
| `--dry-run` | `false` | Preview without writing files |
