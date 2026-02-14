# Architecture

## Standards

The tool connects two [Bitol](https://bitol.io/) open standards to dbt:

- **[ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)** (Open Data Product Standard) -- defines data products with input/output ports, each referencing a contract by `contractId`
- **[ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)** (Open Data Contract Standard) -- defines data schemas (tables, columns, types), quality rules, and SLA properties

## Generation pipeline

1. **Parse** -- read ODPS product files and extract input/output ports
2. **Resolve** -- match each port's `contractId` to an ODCS contract file
3. **Export** -- generate dbt artifacts (sources, models, staging SQL) via `datacontract-cli`
4. **Post-process** -- rename sources to match port names, merge per-contract exports into single files, and rewire `source()` references using `inputContracts` lineage

## ODPS to dbt mapping

| ODPS concept | dbt artifact |
|-------------|-------------|
| Input port | `sources.yml` entry (source name = port name) |
| Output port | `models/schema.yml` entry (model + column definitions) |
| Output port with schema | `models/staging/stg_<table>.sql` (staging SQL) |
| `inputContracts` on output port | `{{ source() }}` refs in staging SQL |
