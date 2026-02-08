# AGENTS.md

Project instructions for Agents working on `dbt-contracts`.

## Project Overview

Contract-driven dbt workflow tool that uses Bitol ODPS (Open Data Product Standard) v1.0.0 and Bitol ODCS (Open Data Contract Standard) v3.1.0 to generate dbt models, sources, and tests. See `docs/implementation-plan.md` for the full architecture and open issues.

## Environment Setup

- **Package manager**: `uv` (from Astral) — never use `pip` directly
- **Python version**: see `.python-version`
- **Build system**: `uv_build`
- **Bootstrap**: `just install` (runs `uv sync --dev` + installs pre-commit hooks)

## Key Commands

| Command | Purpose |
|---------|---------|
| `just install` | Sync dependencies + install pre-commit hooks |
| `just test` | Run pytest (`uv run -m pytest -q`) |
| `just check` | Run all pre-commit hooks (ruff, ruff-format, ty, hygiene) |
| `just lint` | Run ruff only |
| `just typing` | Run ty type checker only |
| `just docs` | Build docs with zensical |
| `just run` | Run the application |
| `just clean` | Remove `.venv`, caches, `__pycache__` |
| `just update` | Upgrade lock file (`uv lock --upgrade`) |
| `uv add <pkg>` | Add runtime dependency |
| `uv add --dev <pkg>` | Add dev dependency |

## Code Quality Rules

**Always run `just check` and `just test` before considering work complete.**

- **Type hints** on all function signatures
- **PEP 257 docstrings** on all public functions/classes — concise, focused on intent
- **Line length**: 120 characters max
- **Indentation**: 4 spaces
- **Imports**: use built-in collection types (`list[str]`, `dict[str, int]`), PEP 604 unions (`str | None`)
- **Ruff rules**: `D` (docstrings), `E4`, `E7`, `E9`, `F` — see `pyproject.toml`
- **Docstring convention**: PEP 257 (via ruff)
- Treat ruff, ty, and pytest warnings as failures — resolve before finalizing

## Pre-commit Hooks

Pre-commit runs automatically on `git commit`. The hooks are:
- `check-case-conflict`, `check-merge-conflict`, `check-toml`, `check-yaml`, `check-json`
- `pretty-format-json`, `end-of-file-fixer`, `trailing-whitespace`
- `ruff` (lint + fix) and `ruff-format`
- `ty-check` (type checking)

## Testing

- Framework: `pytest`
- Tests live in `tests/`
- Test files follow `test_*.py` naming
- Keep tests focused and deterministic
- Test critical paths and edge cases (empty inputs, invalid types, missing files)

## Dependency Management

- Add runtime deps: `uv add <package>`
- Add dev deps: `uv add --dev <package>`
- After changing deps: commit `pyproject.toml` and `uv.lock`, then run `just check` and `just test`
- The `pylock.toml` is auto-exported by `just install` and `just update`

## Observability

- Logging uses Pydantic Logfire (`logfire`)
- Configure via `.env` file (copy `.env.example`), set `LOGFIRE_TOKEN`
- If no token, logs go to console only (`send_to_logfire='if-token-present'`)

## Project Structure

```
src/dbt_contracts/          # Main package (being built)
├── odps/                   # ODPS v1.0.0 parsing (our code, no official lib)
├── odcs/                   # ODCS v3.1.0 integration (uses open-data-contract-standard)
├── generators/             # dbt artifact generation (wraps datacontract-cli)
├── commands/               # CLI command implementations
├── cli.py                  # Click-based CLI entry point
├── config.py               # Configuration loading
└── interactive.py          # Interactive mode UI
tests/                      # pytest tests
docs/                       # Documentation + implementation plan
```

## Key Dependencies

| Package | Role |
|---------|------|
| `open-data-contract-standard` | Official ODCS v3.1.0 Pydantic models |
| `datacontract-cli` | Contract validation (lint/test) + dbt export |
| `pydantic` | ODPS Pydantic models (custom, no official lib) |
| `pyyaml` | YAML parsing for ODPS files |
| `click` | CLI framework |
| `rich` + `questionary` | Interactive terminal UI |

## Standards References

- ODPS v1.0.0: https://bitol-io.github.io/open-data-product-standard/v1.0.0/
- ODCS v3.1.0: https://bitol-io.github.io/open-data-contract-standard/v3.1.0/
- ODCS uses **Objects** (tables) and **Properties** (columns) — not "schemas" and "columns"
- ODCS properties have `logicalType` + `physicalType` — not a single "data type"
- datacontract-cli docs: https://cli.datacontract.com/
