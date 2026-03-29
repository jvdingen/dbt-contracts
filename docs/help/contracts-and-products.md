# Contracts and products

## "Unknown field" in contract YAML

The ODCS SDK uses `extra='forbid'`, meaning any unrecognized fields will cause a validation error. Check for typos in field names against the [ODCS v3.1.0 specification](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/).

Common mistakes:

- `datatype` instead of `logicalType` or `physicalType`
- `owner` at the top level instead of inside `team`
- `tests` instead of `quality` for quality checks

## "contractId not found" in product validation

This means an ODPS product references a contract ID that doesn't exist in any `.odcs.yaml` file. Check that:

1. The referenced contract file exists in `contracts/contracts/`
2. The `id` field in the contract matches the `contractId` in the product
3. The contract file has the `.odcs.yaml` extension

This check can be disabled with `validation.cross_reference: false` in `config.yaml`.

## Status below minimum threshold

If validation reports a status error, one of your contracts has a status lower than the configured `validation.min_status`. For example, a `proposed` contract will fail if `min_status` is `draft`. Either promote the contract's status or lower the threshold in `config.yaml`.
