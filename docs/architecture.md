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
│  │          │  │          │  │               │  │
│  │ Scan &   │  │ Schema   │  │ Models, YAML, │  │
│  │ load     │  │ & xref   │  │ SQL, tests    │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
├─────────────────────────────────────────────────┤
│                  Models                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Config   │  │ ODPS     │  │ ODCS (SDK)    │  │
│  │ (custom) │  │ (custom) │  │               │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
└─────────────────────────────────────────────────┘
```

## Data flow

### 1. Discovery

The discovery module scans the `contracts/` directory:

- `contracts/contracts/*.odcs.yaml` — loaded via the `open-data-contract-standard` SDK
- `contracts/products/*.odps.yaml` — loaded via custom ODPS Pydantic models
- `contracts/config.yaml` — loaded via custom Config Pydantic model

### 2. Validation

Validation runs in two passes:

1. **Schema validation** — Each contract and product is validated against its respective standard (ODCS v3.1.0, ODPS v1.0.0)
2. **Cross-reference validation** — All `contractId` fields in ODPS products are checked against loaded ODCS contract IDs

### 3. Generation

The generator maps ODCS constructs to dbt artifacts:

| ODCS | dbt |
|---|---|
| SchemaObject | Model (SQL file + schema.yml entry) |
| SchemaProperty | Column in schema.yml |
| Server | Source in sources.yml |
| `primaryKey: true` | `unique` + `not_null` tests |
| `required: true` | `not_null` test |
| `unique: true` | `unique` test |
| Quality check (`nullValues`) | `not_null` test |
| Quality check (`duplicateValues`) | `unique` test |
| Quality check (`rowCount`) | Custom test |
| `description` | `description` field |
| `slaProperties` | `meta` fields |
| `team` | `meta.owners` field |

## Standards

dbt-contracts is built on two open standards from the [Bitol](https://bitol.io/) organization (Linux Foundation AI & Data):

- **[ODCS v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)** — Defines data contracts (shape, quality, SLAs)
- **[ODPS v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/)** — Defines data products (ports, ownership, governance)

The ODCS SDK (`open-data-contract-standard` on PyPI) provides Pydantic v2 models for parsing and validating contracts. The ODPS models are hand-rolled following the same methodology.
