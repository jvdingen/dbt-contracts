# Troubleshooting

Common issues and their solutions.

## Installation

### `pip install` fails with dependency conflicts

Ensure you're using Python 3.10 or later:

```bash
python --version
```

If using uv:

```bash
uv add dbt-contracts
```

## Validation errors

### "Unknown field" in contract YAML

The ODCS SDK uses `extra='forbid'`, meaning any unrecognized fields will cause a validation error. Check for typos in field names against the [ODCS v3.1.0 specification](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/).

### "contractId not found" in product validation

This means an ODPS product references a contract ID that doesn't exist in any `.odcs.yaml` file. Check that:

1. The referenced contract file exists in `contracts/contracts/`
2. The `id` field in the contract matches the `contractId` in the product
3. The contract file has the `.odcs.yaml` extension

This check can be disabled with `validation.cross_reference: false` in `config.yaml`.

## Generation

### Generated models overwrite my changes

By default, `dbt-contracts generate` will not overwrite files that don't contain the generated header comment. If your file was overwritten, it still contained the header --- meaning it was treated as a managed file. To prevent overwriting, remove the header comment from files you want to maintain manually.

Use `dbt-contracts diff` to preview what would change before running `generate` or `sync`.

### Wrong SQL dialect in generated models

Check the `servers` field in your contract. The server type (e.g., `snowflake`, `bigquery`, `postgres`) determines the SQL dialect and type mappings. If a contract has no `servers` entry, the `default_server_type` from `config.yaml` is used.

## Diff and sync

### `diff` always shows drift

If `dbt-contracts diff` reports changes even right after `generate`, check that no other tool (e.g., a formatter or pre-commit hook) is modifying the generated files. The diff comparison is byte-exact.

### `sync` asks for confirmation

By default, `sync` shows a preview and asks for confirmation. Use `--yes` to skip the prompt, which is useful in CI/CD pipelines.

## Import

### Imported contracts are incomplete

`dbt-contracts import` generates draft contract stubs. These capture column names, types, and basic constraints (`not_null`, `unique`) from your dbt YAML, but won't include quality rules, SLAs, team info, or lineage. You'll need to add those manually.

Imported contracts have `status: draft` by default. Update the status as you refine them.

## Getting help

- [GitHub Issues](https://github.com/jvdingen/dbt-contracts/issues) --- Bug reports and feature requests
- [ODCS Specification](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) --- Contract standard reference
- [ODPS Specification](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) --- Product standard reference
