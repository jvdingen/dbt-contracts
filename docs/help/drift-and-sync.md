# Drift detection and sync

## `diff` always shows drift

If `dbt-contracts diff` reports changes even right after `generate`, check that no other tool (e.g., a formatter or pre-commit hook) is modifying the generated files. The diff comparison is byte-exact --- any whitespace or formatting change counts as drift.

## `sync` asks for confirmation

By default, `sync` shows a preview and asks for confirmation. Use `--yes` to skip the prompt, which is useful in CI/CD pipelines:

```bash
dbt-contracts sync --contracts-dir contracts --yes
```

## `diff` exits with code 1

This is expected behavior. `diff` exits with code 1 when drift is detected, making it easy to use as a CI gate:

```bash
dbt-contracts diff --contracts-dir contracts --format json
```
