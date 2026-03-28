# Architecture

This document describes how dbt-contracts works under the hood.

## Overview

dbt-contracts is a pipeline that reads data contract definitions and produces dbt project artifacts:

```
ODCS Contracts (.odcs.yaml)  ─┐
                               ├─→ Validate ─→ Generate ─→ dbt Project
ODPS Products (.odps.yaml)   ─┘
```

## Component architecture

```
┌─────────────────────────────────────────────────┐
│                  CLI (click)                     │
│  dbt-contracts                                   │
├─────────────────────────────────────────────────┤
│                  Core                            │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Discovery│  │Validation│  │  Generation    │  │
│  │ Scan &   │  │ Schema   │  │ Post-process  │  │
│  │ load     │  │ & xref   │  │ & write files │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Differ  │  │  Init    │  │  Importer     │  │
│  │ Drift    │  │ Scaffold │  │ dbt → ODCS    │  │
│  │ detect   │  │ project  │  │ contracts     │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │              Adapter                        │  │
│  │  lint() ─ ODCS validation                   │  │
│  │  render() ─ lineage-aware dbt generation    │  │
│  │  Wraps datacontract-cli exporters           │  │
│  └────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│                  Models                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Config   │  │ ODPS     │  │ ODCS (SDK)    │  │
│  │ (custom) │  │ (custom) │  │               │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
├─────────────────────────────────────────────────┤
│             External Libraries                   │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ datacontract-cli │  │ open-data-contract-  │  │
│  │ (dbt exporters,  │  │ standard (ODCS SDK)  │  │
│  │  linting)        │  │                      │  │
│  └──────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Data flow

### 1. Discovery

The discovery module scans the `contracts/` directory:

- `contracts/contracts/*.odcs.yaml` — loaded via the `open-data-contract-standard` SDK
- `contracts/products/*.odps.yaml` — loaded via custom ODPS Pydantic models
- `contracts/config.yaml` — loaded via custom Config Pydantic model

### 2. Validation

Validation runs in three passes:

1. **Schema validation** — Each ODCS contract is validated against the JSON schema via the adapter's `lint()` function (delegates to datacontract-cli)
2. **Cross-reference validation** — All `contractId` fields in ODPS products are checked against loaded ODCS contract IDs (gated by `validation.cross_reference` config)
3. **Status checks** — Contract statuses are checked against the `validation.min_status` threshold

### 3. Adapter (rendering)

The adapter layer (`core/adapter.py`) wraps datacontract-cli's dbt exporters and adds lineage awareness:

1. **Lineage classification** — Uses ODPS ports to classify each contract:
   - `outputPorts.contractId` → **model** (gets model YAML + staging SQL)
   - `inputPorts.contractId` → **source** (gets sources YAML)
   - `inputPorts` that are also `outputPorts` of another ODPS → **ref** (referenced via `{{ ref() }}` instead of `{{ source() }}`)
   - Contracts not in any port → **source** (default)

2. **Per-contract rendering** — Calls datacontract-cli's `DbtExporter` or `DbtSourceExporter` per contract, resolving server type from the contract's `servers` definition

3. **Staging SQL** — Builds SQL referencing upstream contracts. Uses `{{ source() }}` for pure sources and `{{ ref() }}` for contracts that are outputs of other data products

Returns a `GenerationResult` with parsed dicts for sources, models, and staging SQL strings.

### 4. Generation

The generator takes the adapter's output and:

| Adapter output | dbt artifact |
|---|---|
| `result.sources` | `sources.yml` per source contract |
| `result.models` | `schema.yml` per model contract (columns, types, tests, constraints) |
| `result.staging_sql` | `stg_*.sql` per model schema object |

The datacontract-cli exporters handle the heavy mapping:

| ODCS | dbt |
|---|---|
| SchemaObject | Model (SQL file + schema.yml entry) |
| SchemaProperty | Column in schema.yml |
| Server | Source in sources.yml |
| `primaryKey: true` | `unique` + `not_null` constraints/tests |
| `required: true` | `not_null` constraint/test |
| `unique: true` | `unique` constraint/test |
| `logicalTypeOptions.pattern` | `dbt_expectations.expect_column_values_to_match_regex` |
| `logicalTypeOptions.minimum/maximum` | `dbt_expectations.expect_column_values_to_be_between` |
| `logicalTypeOptions.minLength/maxLength` | `dbt_expectations.expect_column_value_lengths_to_be_between` |
| `relationships` | `relationships` test |
| Composite primary keys | `dbt_utils.unique_combination_of_columns` |
| `description` | `description` field |
| `team` | `meta.owner` field |

### 5. Diff and sync

The differ (`core/differ.py`) generates expected output in memory (via a dry-run generate) and compares each file with its on-disk counterpart. Each file is classified as **new**, **modified**, or **unchanged**. The `sync` command applies detected drift by re-running generation with `force=True`.

### 6. Import

The importer (`core/importer.py`) reads existing dbt `schema.yml` files and generates ODCS contract stubs. It handles both `sources` and `models` definitions, mapping columns, constraints, and data_tests back to ODCS properties.

## Standards

dbt-contracts is built on two open standards from the [Bitol](https://bitol.io/) organization (Linux Foundation AI & Data):

- **[ODCS v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)** — Defines data contracts (shape, quality, SLAs)
- **[ODPS v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)** — Defines data products (ports, ownership, governance)

The ODCS SDK (`open-data-contract-standard` on PyPI) provides Pydantic v2 models for parsing and validating contracts. The ODPS models are hand-rolled following the same methodology. The `datacontract-cli` library provides dbt export and linting capabilities.
