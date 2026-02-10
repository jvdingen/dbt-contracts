# dbt-contracts

Contract-driven dbt workflow tool using [ODPS](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) and [ODCS](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) to generate dbt models, sources, and tests.

## Overview

ODPS (Open Data Product Standard) files define **data products** with input and output ports. Each port references an ODCS (Open Data Contract Standard) contract via `contractId`. This tool parses those definitions and generates dbt artifacts.

- **Input ports** become dbt sources
- **Output ports** become dbt models with schema definitions and tests

## Implemented Modules

### ODPS Parsing

::: dbt_contracts.odps.schema

::: dbt_contracts.odps.parser

### ODCS Integration

::: dbt_contracts.odcs.parser

::: dbt_contracts.odcs.validator
