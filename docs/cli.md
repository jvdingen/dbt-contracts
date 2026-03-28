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

*Available in Phase 5.*

Generate dbt models, schema files, and tests from validated contracts.

```bash
dbt-contracts generate [--contracts-dir PATH] [--output-dir PATH] [--force]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--contracts-dir` | `./contracts` | Path to the contracts directory |
| `--output-dir` | From config `generation.models_dir` | Path to the dbt models output directory |
| `--force` | `false` | Overwrite existing files without confirmation |

### `init`

*Available in Phase 6.*

Initialize a `contracts/` directory in the current dbt project with sample files.

```bash
dbt-contracts init [--dir PATH]
```

### `bootstrap`

*Available in Phase 6.*

Create a new dbt project from scratch using contracts.

```bash
dbt-contracts bootstrap [--name NAME] [--contracts-dir PATH]
```

### `diff`

*Available in Phase 7.*

Show differences between contracts and the current dbt project state.

```bash
dbt-contracts diff [--contracts-dir PATH]
```

### `sync`

*Available in Phase 7.*

Update the dbt project to match the current contracts.

```bash
dbt-contracts sync [--contracts-dir PATH] [--force]
```

### `import`

*Available in Phase 7.*

Generate ODCS contracts from an existing dbt `schema.yml`.

```bash
dbt-contracts import [--schema PATH] [--output-dir PATH]
```
