# Import

## Imported contracts are incomplete

`dbt-contracts import` generates draft contract stubs. These capture column names, types, and basic constraints (`not_null`, `unique`) from your dbt YAML, but won't include quality rules, SLAs, team info, or lineage. You'll need to add those manually.

Imported contracts have `status: draft` by default. Update the status as you refine them.

## Import doesn't detect all constraints

For **sources**, only `data_tests` are detected (`not_null`, `unique`). For **models**, both `data_tests` and `constraints` are detected. This matches dbt's own feature split --- sources don't support column-level constraints.
