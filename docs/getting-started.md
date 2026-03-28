# Getting Started

## Installation

### With pip

```bash
pip install dbt-contracts
```

### With uv

```bash
uv add dbt-contracts
```

### From source

```bash
git clone https://github.com/jvdingen/dbt-contracts.git
cd dbt-contracts
just install
```

## Prerequisites

- Python 3.10 or later
- An existing dbt project (for `init`, `validate`, `generate`, `sync` commands)
- Or use `import` to generate contracts from an existing dbt `schema.yml`

## Your first contract

### 1. Initialize the contracts directory

Navigate to your dbt project and run:

```bash
dbt-contracts init
```

This creates the `contracts/` directory with a default configuration:

```
contracts/
├── config.yaml
├── contracts/
└── products/
```

### 2. Create a contract

Create a file at `contracts/contracts/orders.odcs.yaml`:

```yaml
kind: DataContract
apiVersion: v3.1.0
id: 53581432-6c55-4ba2-a65f-72344a91553a
name: Orders
domain: commerce
version: 1.0.0
status: active

schema:
  - name: orders
    physicalName: stg_orders
    properties:
      - name: order_id
        logicalType: string
        primaryKey: true
        required: true
      - name: customer_id
        logicalType: string
        required: true
      - name: order_date
        logicalType: date
        required: true
        quality:
          - metric: nullValues
            mustBe: 0
            type: library
            severity: error
      - name: total_amount
        logicalType: number
```

### 3. Validate

```bash
dbt-contracts validate
```

### 4. Generate dbt models

```bash
dbt-contracts generate
```

This creates the corresponding dbt model files, schema definitions, and tests.

## CLI aliases

The tool is also available as `dbtc` for convenience:

```bash
# These are equivalent
dbt-contracts validate
dbtc validate
```

## Importing from existing dbt projects

Already have a dbt project with `schema.yml` files? Generate contract stubs:

```bash
dbt-contracts import models/schema.yml --output-dir contracts/contracts
```

Then refine the generated contracts and add ODPS product definitions.

## Next steps

- [CLI Reference](cli.md) — Full command documentation
- [Contracts Guide](contracts.md) — Deep dive into ODCS contracts
- [Products Guide](products.md) — Working with ODPS data products
