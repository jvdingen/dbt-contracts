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

## Generation

### Generated models overwrite my changes

By default, `dbt-contracts generate` will not overwrite files that have been modified. Use `--force` to override this behavior, or use `dbt-contracts diff` to see what would change before generating.

### Wrong SQL dialect in generated models

Check the `servers` field in your contract and `default_server_type` in `contracts/config.yaml`. The server type determines the SQL dialect used in generation.

## Getting help

- [GitHub Issues](https://github.com/jvdingen/dbt-contracts/issues) — Bug reports and feature requests
- [ODCS Specification](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) — Contract standard reference
- [ODPS Specification](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) — Product standard reference
