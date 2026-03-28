# Contracts Guide

dbt-contracts uses the [Open Data Contract Standard (ODCS) v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) for defining data contracts. This guide covers how to write contracts for use with dbt-contracts.

## File conventions

- Contract files must have the `.odcs.yaml` extension
- Place contracts in `contracts/contracts/` within your dbt project
- Each file defines a single data contract

## Contract structure

A minimal contract:

```yaml
kind: DataContract
apiVersion: v3.1.0
id: <uuid>
version: 1.0.0
status: active

schema:
  - name: my_table
    properties:
      - name: id
        logicalType: integer
        primaryKey: true
```

## Required fields

| Field | Description |
|---|---|
| `kind` | Must be `"DataContract"` |
| `apiVersion` | Must be `"v3.1.0"` |
| `id` | Unique UUID for this contract |
| `version` | Semantic version of the contract |
| `status` | One of: `proposed`, `draft`, `active`, `deprecated`, `retired` |

## Schema

The `schema` field is an array of schema objects (tables/datasets). Each schema object contains:

- `name` — Logical name used in dbt
- `physicalName` — Actual table name in the database
- `description` — What this table represents
- `dataGranularityDescription` — What each row represents
- `properties` — Array of columns

### Column properties

Each column in `properties` supports:

| Field | Description | dbt mapping |
|---|---|---|
| `name` | Column name | Column name in schema.yml |
| `logicalType` | Data type (string, integer, date, etc.) | Column data type |
| `physicalType` | Database-specific type | Used in SQL generation |
| `description` | Column description | `description` in schema.yml |
| `primaryKey` | Is this a primary key? | `unique` + `not_null` tests |
| `required` | Is this column required? | `not_null` test |
| `unique` | Must values be unique? | `unique` test |
| `quality` | Quality checks | dbt tests |

## Quality checks

Quality checks on columns or tables map to dbt tests:

```yaml
quality:
  - metric: nullValues
    mustBe: 0
    type: library
    severity: error
  - metric: rowCount
    mustBeGreaterThan: 1000
    type: library
```

See [Architecture](architecture.md) for the full quality-to-dbt-test mapping.

## Servers

The `servers` field tells dbt-contracts which database platform to target:

```yaml
servers:
  - server: production
    type: snowflake
    account: myorg.us-east-1
    warehouse: ANALYTICS_WH
    database: PROD
    schema: PUBLIC
```

Supported server types include: snowflake, bigquery, postgres, redshift, databricks, and [30+ more](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/).

## Team and ownership

```yaml
team:
  name: Commerce Data Team
  members:
    - username: jsmith
      role: Data Owner
    - username: ajones
      role: Data Steward
```

Team information is embedded as metadata in generated dbt schema files.

## SLA properties

```yaml
slaProperties:
  - property: latency
    value: 4
    unit: h
  - property: retention
    value: 7
    unit: y
```

SLA properties are embedded as `meta` fields in dbt models.

## Full example

See the [ODCS specification](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) for a comprehensive example with all supported fields.
