# Contract Parsing

Parsing and validation of ODPS product definitions and ODCS data contracts.

## ODPS

### Schema models

Pydantic models representing the ODPS data product structure (ports, contracts, lineage).

::: dbt_contracts.odps.schema

### Parser

Discovers and parses `*.odps.yaml` files from the configured products directory.

::: dbt_contracts.odps.parser

## ODCS

### Parser

Discovers and parses `*.odcs.yaml` files, resolving contract references by ID.

::: dbt_contracts.odcs.parser

### Validator

Lints contracts for structural correctness or runs live data tests.

::: dbt_contracts.odcs.validator
