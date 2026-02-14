# Contracts Guide

`dbt-contracts` uses two Bitol open standards to describe data products and their schemas.

## ODPS -- Data Product Definitions

[ODPS (Open Data Product Standard) v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) files define **data products** with input and output ports. Each port references a contract by `contractId`.

Place these in `contracts/products/` with the `.odps.yaml` extension.

```yaml
# contracts/products/my_product.odps.yaml
apiVersion: v1.0.0
kind: DataProduct
name: Customer Data Product
id: fbe8d147-28db-4f1d-bedf-a3fe9f458427
domain: seller
status: draft

inputPorts:
  - name: payments
    version: 1.0.0
    contractId: dbb7b1eb-7628-436e-8914-2a00638ba6db

outputPorts:
  - name: customersummary
    description: Customer Summary
    type: tables
    version: 1.0.0
    contractId: a1234567-b890-cdef-1234-567890abcdef
    inputContracts:
      - id: dbb7b1eb-7628-436e-8914-2a00638ba6db
        version: 1.0.0
```

### Key fields

- **`inputPorts`** -- data sources consumed by this product. Each becomes a dbt source.
- **`outputPorts`** -- data this product produces. Each becomes a dbt model.
- **`contractId`** -- links a port to an ODCS contract file. Must match the `id` field of a `.odcs.yaml` file.
- **`inputContracts`** -- on output ports, declares which input contracts feed into this output. Used to generate `{{ source() }}` refs in staging SQL.

## ODCS -- Data Contracts

[ODCS (Open Data Contract Standard) v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/) files define the actual data schema: tables, columns, types, and quality rules.

Place these in `contracts/schemas/` with the `.odcs.yaml` extension.

```yaml
# contracts/schemas/payments.odcs.yaml
kind: DataContract
apiVersion: v3.1.0
id: dbb7b1eb-7628-436e-8914-2a00638ba6db
name: Payments Contract
version: 1.0.0
status: active

schema:
  - name: payments
    physicalName: raw_payments
    physicalType: table
    description: Payment transaction records
    properties:
      - name: payment_id
        logicalType: string
        physicalType: varchar
        primaryKey: true
        required: true
        description: Unique payment identifier
      - name: customer_id
        logicalType: string
        physicalType: varchar
        required: true
        description: Reference to the customer
      - name: amount
        logicalType: number
        physicalType: decimal
        required: true
        description: Payment amount in cents
```

```yaml
# contracts/schemas/customer_summary.odcs.yaml
kind: DataContract
apiVersion: v3.1.0
id: a1234567-b890-cdef-1234-567890abcdef
name: Customer Summary Contract
version: 1.0.0
status: active

schema:
  - name: customer_summary
    physicalName: customer_summary
    physicalType: table
    description: Aggregated customer metrics
    properties:
      - name: customer_id
        logicalType: string
        physicalType: varchar
        primaryKey: true
        required: true
        description: Unique customer identifier
      - name: total_payments
        logicalType: number
        physicalType: decimal
        required: true
        description: Total payment amount
      - name: last_payment_date
        logicalType: timestamp
        physicalType: timestamp
        required: false
        description: Date of most recent payment
```

### Schema properties

| Property | Description |
|----------|-------------|
| `primaryKey: true` | Generates a `unique` dbt test |
| `required: true` | Generates a `not_null` dbt test |
| `physicalName` | Used as the table/column name in generated dbt artifacts |
| `logicalType` | Logical data type (string, number, timestamp, etc.) |
| `physicalType` | Database-specific type (varchar, decimal, etc.) |

## File naming conventions

| File type | Extension | Directory |
|-----------|-----------|-----------|
| ODPS data products | `*.odps.yaml` | `contracts/products/` |
| ODCS data contracts | `*.odcs.yaml` | `contracts/schemas/` |

These extensions are required -- the tool uses them to discover files. Both directories are searched recursively.
