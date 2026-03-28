# dbt-contracts

**Contract-first dbt development using open standards.**

dbt-contracts generates and manages dbt projects from data contracts. Define your data shape, quality rules, and lineage in ODCS/ODPS YAML files, and let dbt-contracts produce the models, sources, staging SQL, and tests.

## The workflow

```
  Define          Validate         Generate         Maintain
  ┌──────┐       ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ ODCS │──────>│ validate │────>│ generate │────>│ diff     │
  │ ODPS │       │          │     │          │     │ sync     │
  └──────┘       └──────────┘     └──────────┘     └──────────┘
  Contracts       Schema lint      models/*.yml     Detect drift
  & products      Cross-refs       sources/*.yml    Apply changes
                  Status check     stg_*.sql
```

Or start from the other direction --- import existing dbt `schema.yml` files as contract stubs using `dbt-contracts import`.

## Key concepts

**Data contracts (ODCS)** define the promise about your data: what columns exist, their types, quality rules, who owns it, and what SLAs apply. Each contract maps to one or more dbt models or sources.

**Data products (ODPS)** define how data flows between systems. Input ports reference source contracts, output ports reference model contracts. This lineage determines whether generated SQL uses `{{ source() }}` or `{{ ref() }}`.

**Configuration** (`config.yaml`) controls generation behavior: output directories, whether to include tests, validation settings, and the default server type.

## Guides

| Guide | What you'll learn |
|---|---|
| [Getting Started](getting-started.md) | Install, create your first contract, generate dbt models |
| [Contracts](contracts.md) | Writing ODCS contracts: schema, quality, servers, team |
| [Products](products.md) | Writing ODPS products: ports, lineage, cross-references |
| [Configuration](configuration.md) | All `config.yaml` options and defaults |

## Reference

| Reference | What's covered |
|---|---|
| [CLI](cli.md) | All commands, options, flags, and exit codes |
| [Architecture](architecture.md) | How it works: discovery, validation, rendering, generation |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
