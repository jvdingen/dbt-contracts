# Architecture

## Standards

The tool connects two [Bitol](https://bitol.io/) open standards to dbt:

- **[ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)** (Open Data Product Standard) -- defines data products with input/output ports, each referencing a contract by `contractId`
- **[ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)** (Open Data Contract Standard) -- defines data schemas (tables, columns, types), quality rules, and SLA properties

## Generation pipeline

```
ODPS product file (.odps.yaml)
        │
        ▼
┌─────────────────┐
│  Parse product   │  Extract input & output ports
└────────┬────────┘
         ▼
┌─────────────────┐
│ Resolve contracts│  Match each port's contractId → .odcs.yaml file
└────────┬────────┘
         ▼
┌─────────────────┐
│  Export to dbt   │  datacontract-cli generates sources & model schemas
└────────┬────────┘
         ▼
┌─────────────────┐
│  Generate SQL    │  Build model SQL with source()/ref() from lineage
└────────┬────────┘
         ▼
┌─────────────────┐
│  Post-process    │  Rename sources, merge files
└────────┬────────┘
         ▼
┌─────────────────┐
│  Drift detection │  Compare against existing files on disk
└────────┬────────┘
         ▼
   Generated files
   (NEW / UNCHANGED / CHANGED)
```

### Contract resolution

Each port in an ODPS product references a contract by `contractId` (a UUID). The resolver scans `odcs_dir` recursively for all `.odcs.yaml` files, reads their `id` field, and returns the first match. If no contract matches, a `FileNotFoundError` is raised.

### Export

For each **input port**, the resolved contract is exported to a dbt `sources.yml` entry via `datacontract-cli` (unless the input is another product's output, in which case it becomes a `ref()`). For each **output port**, the contract is exported to a `schema.yml` model definition and (if the contract has a `schema` section) a `<table>.sql` model SQL file.

### Post-processing

The raw exports use contract UUIDs as source names, which aren't human-readable. Post-processing applies two transformations:

1. **Source renaming** -- replace the contract UUID with the port name (e.g. `a1b2c3d4-...` becomes `payments_source`)
2. **File merging** -- per-contract exports are merged into a single `sources.yml` and a single `schema.yml`, each with `version: 2` and a combined list

Model SQL is generated directly by the orchestrator (not exported from datacontract-cli). The `inputContracts` list on each output port determines whether to use `{{ source() }}` (for raw data sources) or `{{ ref() }}` (for other products' outputs).

### Drift detection

`plan_for_product()` generates all files in memory without writing to disk. Each file is then compared against the existing file at its target path:

- **NEW** -- file doesn't exist yet, will be written directly
- **UNCHANGED** -- generated content matches the existing file exactly, skipped
- **CHANGED** -- content differs from the existing file, shown as a unified diff

This lets `generate` show you exactly what changed before overwriting anything.

## ODPS to dbt mapping

| ODPS concept | dbt artifact |
|-------------|-------------|
| Input port | `sources.yml` entry (source name = port name) |
| Output port | `models/schema.yml` entry (model + column definitions) |
| Output port with schema | `models/<table>.sql` (model SQL) |
| `inputContracts` on output port | `{{ source() }}` or `{{ ref() }}` in model SQL |

## Example output

A product with one input port (`raw_payments`) and one output port (`clean_payments`) generates:

**`sources/sources.yml`**
```yaml
version: 2
sources:
  - name: raw_payments
    tables:
      - name: payments
        columns:
          - name: id
            data_type: VARCHAR
```

**`models/schema.yml`**
```yaml
version: 2
models:
  - name: payments
    columns:
      - name: id
        data_type: VARCHAR
        tests:
          - not_null
```

**`models/payments.sql`**
```sql
select
    id
from {{ source('raw_payments', 'payments') }}
```
