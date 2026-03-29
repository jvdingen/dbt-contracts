# Generation

## Generated models overwrite my changes

By default, `dbt-contracts generate` will not overwrite files that don't contain the generated header comment. If your file was overwritten, it still contained the header --- meaning it was treated as a managed file. To prevent overwriting, remove the header comment from files you want to maintain manually.

Use `dbt-contracts diff` to preview what would change before running `generate` or `sync`.

## Wrong SQL dialect in generated models

Check the `servers` field in your contract. The server type (e.g., `snowflake`, `bigquery`, `postgres`) determines the SQL dialect and type mappings. If a contract has no `servers` entry, the `default_server_type` from `config.yaml` is used.

## No files generated

If `generate` runs without errors but produces no files, check that:

- Your contracts have a `schema` section with at least one schema object
- Your ODPS products have `outputPorts` with valid `contractId` references (otherwise contracts default to sources, not models)
- `generation.generate_sources` is not set to `false` if you're expecting source files
