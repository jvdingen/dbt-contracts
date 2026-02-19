# CLI Reference

## Global options

```
dbt-contracts [OPTIONS] COMMAND
```

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to a specific config file (overrides auto-discovery) |
| `--verbose` | Enable verbose output -- shows additional detail during execution (e.g. which files are being processed, contract resolution steps, export progress) |
| `--help` | Show help and exit |

## `init`

Scaffold a new project with a complete dbt project structure. Creates config file at `contracts/dbt-contracts.toml`, `dbt_project.yml`, `profiles.yml`, and all standard dbt directories. Safe to run multiple times -- skips existing files.

When an existing `dbt_project.yml` is detected, only creates the `contracts/` folder with configuration -- skips dbt project scaffolding. Reads `model-paths` from the existing project and prompts for confirmation.

```sh
# Interactive — prompts for database adapter
dbt-contracts init

# Non-interactive — specify adapter directly
dbt-contracts init --adapter duckdb
dbt-contracts init --adapter postgres
dbt-contracts init --adapter snowflake
dbt-contracts init --adapter bigquery
```

| Option | Description |
|--------|-------------|
| `--adapter` | Database adapter for `profiles.yml` (`duckdb`, `postgres`, `snowflake`, `bigquery`) |

The scaffolded project structure:

```
├── dbt_project.yml             ← dbt project config
├── profiles.yml                ← dbt connection profile
├── contracts/
│   ├── dbt-contracts.toml      ← dbt-contracts config
│   ├── products/               ← ODPS product files go here
│   └── schemas/                ← ODCS contract files go here
├── models/
│   ├── <table>.sql             ← generate writes model SQL here
│   └── schema.yml              ← generate writes model schema here
├── sources/
│   └── sources.yml             ← generate writes source defs here
├── macros/
├── seeds/
├── tests/
├── analyses/
└── snapshots/
```

## `generate`

![Generate with drift detection](assets/gifs/generate-drift.gif)

Generate dbt artifacts from ODPS product definitions. The command is **drift-aware**: it compares generated output against existing files on disk and reports what changed.

- **New files** are written directly without prompting.
- **Unchanged files** are skipped silently.
- **Changed files** show a unified diff and prompt per-file (Yes / No / Yes to all remaining).

```sh
# Generate from all products (prompts for changed files)
dbt-contracts generate

# Generate from one specific product file
dbt-contracts generate --product my_product.odps.yaml

# Preview what would be generated without writing files
dbt-contracts generate --dry-run

# Auto-accept all changes without prompting
dbt-contracts generate --yolo-mode
```

| Option | Description |
|--------|-------------|
| `--product FILE` | Generate from a specific ODPS file (name relative to `odps_dir`, or absolute path) |
| `--dry-run` | Show drift report without writing any files |
| `--yolo-mode` | Auto-accept all changes without prompting |

Exit code is 1 if no files were generated (missing directories, no products found, etc.).

In interactive mode, `--yolo-mode` is ignored — the command always prompts for changed files.

## `validate`

![Validation demo](assets/gifs/validate.gif)

Validate ODCS contracts.

```sh
# Lint all contracts (default)
dbt-contracts validate

# Validate a specific contract
dbt-contracts validate --contract payments.odcs.yaml

# Run live tests against data sources (requires server configuration)
dbt-contracts validate --live
```

| Option | Description |
|--------|-------------|
| `--contract FILE` | Validate a specific ODCS file (name relative to `odcs_dir`, or absolute path) |
| `--live` | Run live data tests instead of offline lint |

Exit code is 1 if any contract fails validation.

## `config`

Inspect and manage configuration.

```sh
# Show resolved configuration as TOML
dbt-contracts config

# Show active config file path
dbt-contracts config path

# Set a configuration value
dbt-contracts config set generation.dry_run true
dbt-contracts config set paths.models_dir build
dbt-contracts config set cli_mode subcommand

# Export resolved config to a file (e.g. to share with your team)
dbt-contracts config export team-config.toml

# Import config from a file
dbt-contracts config import team-config.toml
```

| Subcommand | Description |
|------------|-------------|
| *(none)* | Print the fully resolved configuration as TOML |
| `path` | Show which config file is active, or "none" |
| `set <key> <value>` | Update a value in `contracts/dbt-contracts.toml` (creates the file if needed) |
| `export <path>` | Export the resolved configuration to a TOML file |
| `import <path>` | Import configuration from a TOML file into `contracts/dbt-contracts.toml` |

### Available keys

| Key | Type | Description |
|-----|------|-------------|
| `cli_mode` | `"interactive"` / `"subcommand"` | CLI mode when run without a subcommand |
| `paths.odps_dir` | string | ODPS product directory |
| `paths.odcs_dir` | string | ODCS contract directory |
| `paths.models_dir` | string | dbt models directory |
| `paths.sources_dir` | string | dbt sources directory |
| `generation.dry_run` | boolean | Dry run mode |
| `validation.default_mode` | `"lint"` / `"test"` | Default validation mode |
| `validation.fail_on_error` | boolean | Fail on errors |

Boolean values accept `true`/`false`, `yes`/`no`, `1`/`0`. Constrained string values are validated against their allowed options. Run `config set` with an invalid key to see all available keys with descriptions.

## Interactive mode

![Interactive mode](assets/gifs/interactive.gif)

Running `dbt-contracts` without a subcommand launches an interactive menu (when `cli_mode = "interactive"`, the default):

```
? What would you like to do?
  Initialize project
  Generate dbt artifacts
  Validate contracts
  Configuration
  Exit
```

The generate and validate flows prompt you to select specific files and options.

### Configuration submenu

Selecting **Configuration** opens a submenu:

```
? Configuration
  Show current configuration
  Edit a setting
  Export to file
  Import from file
  Back
```

- **Show current configuration** prints the fully resolved config as TOML.
- **Edit a setting** presents all settings with their current values. Each setting uses the appropriate prompt: yes/no for booleans, a selection list for constrained strings (`cli_mode`, `validation.default_mode`), and free text input (pre-filled with the current value) for paths and directories.
- **Export to file** prompts for a file path and writes the resolved configuration to it.
- **Import from file** prompts for a file path, validates its contents, and writes it to `contracts/dbt-contracts.toml`.

Press Ctrl+C at any prompt to go back.

Set `cli_mode = "subcommand"` in your [configuration](configuration.md) to show help text instead.
