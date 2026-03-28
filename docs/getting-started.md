# Getting Started

## Installation

```bash
pip install dbt-contracts
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add dbt-contracts
```

**Requirements:** Python 3.10 or later.

## Your first contract

### 1. Initialize

Navigate to your dbt project root and run:

```bash
dbt-contracts init
```

This creates:

```
contracts/
├── config.yaml       # Generation and validation settings
├── contracts/        # ODCS contract files go here
└── products/         # ODPS product files go here
```

### 2. Add a contract

Create `contracts/contracts/orders.odcs.yaml`:

```yaml
kind: DataContract
apiVersion: v3.1.0
id: raw-orders
version: 1.0.0
status: active
name: Raw Orders
domain: commerce

servers:
  - server: production
    type: snowflake
    account: acme.us-east-1
    database: RAW
    schema: PUBLIC

schema:
  - name: raw_orders
    description: Raw order data
    physicalType: table
    properties:
      - name: order_id
        logicalType: integer
        physicalType: NUMBER
        primaryKey: true
        required: true
        description: Unique order identifier
      - name: customer_id
        logicalType: integer
        physicalType: NUMBER
        required: true
      - name: amount
        logicalType: number
        physicalType: NUMBER
      - name: created_at
        logicalType: date
        physicalType: TIMESTAMP
```

### 3. Validate

```bash
dbt-contracts validate
```

This checks the contract against the ODCS JSON schema and reports any issues.

### 4. Generate

```bash
dbt-contracts generate
```

This produces dbt artifacts from your contracts:

- **`models/staging/raw-orders.yml`** --- source definition with columns and tests
- **`models/generated/stg_orders.yml`** --- model schema with columns, constraints, and tests
- **`models/generated/stg_orders.sql`** --- staging SQL with `{{ source() }}` references

All generated files include a header comment. On subsequent runs, files with the header are overwritten automatically. Files you've manually edited are skipped unless you pass `--force`.

### 5. Keep in sync

After editing contracts, check what changed:

```bash
dbt-contracts diff
```

Then apply:

```bash
dbt-contracts sync --yes
```

## Starting from an existing dbt project

Already have a dbt project with `schema.yml` files? Import them as contract stubs:

```bash
dbt-contracts import models/schema.yml models/staging/sources.yml \
  --output-dir contracts/contracts
```

This generates draft ODCS contracts from your existing source and model definitions. Refine them, add ODPS product files to define lineage, then use `dbt-contracts generate` to regenerate your dbt project from contracts.

## CLI alias

The tool is also available as `dbtc`:

```bash
dbtc validate    # same as: dbt-contracts validate
```

## Next steps

- [Contracts Guide](contracts.md) --- Deep dive into writing ODCS contracts
- [Products Guide](products.md) --- Defining data products and lineage with ODPS
- [CLI Reference](cli.md) --- All commands and options
- [Configuration](configuration.md) --- Customizing generation and validation
