# Products Guide

dbt-contracts uses the [Open Data Product Standard (ODPS) v1.0.0](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) for defining data products. A data product is the higher-level organizational unit that wraps one or more data contracts.

## File conventions

- Product files must have the `.odps.yaml` extension
- Place products in `contracts/products/` within your dbt project
- Each file defines a single data product

## Relationship to contracts

```
DataProduct (ODPS)
├── InputPort  → references ODCS contract (source data)
├── OutputPort → references ODCS contract (exposed data)
└── ManagementPort → observability, control, discovery
```

A data product describes **what** is being delivered and **how**, while contracts describe the **promise** about the data itself.

## Product structure

A minimal product:

```yaml
kind: DataProduct
apiVersion: v1.0.0
id: <uuid>
status: active
name: Order Analytics

inputPorts:
  - name: raw-orders
    version: 1.0.0
    contractId: <odcs-contract-uuid>

outputPorts:
  - name: analytics-orders
    version: 1.0.0
    contractId: <odcs-contract-uuid>
```

## Required fields

| Field | Description |
|---|---|
| `kind` | Must be `"DataProduct"` |
| `apiVersion` | Must be `"v1.0.0"` |
| `id` | Unique UUID for this product |
| `status` | One of: `proposed`, `draft`, `active`, `deprecated`, `retired` |

## Ports

### Input ports

Where data comes from. Each input port references an ODCS contract that describes the source data.

```yaml
inputPorts:
  - name: raw-orders
    version: 1.0.0
    contractId: 53581432-6c55-4ba2-a65f-72344a91553a
```

### Output ports

What the product exposes to consumers. Each output port can reference an ODCS contract.

```yaml
outputPorts:
  - name: analytics-orders
    version: 1.0.0
    contractId: e4f5a6b7-c8d9-0e1f-2a3b-4c5d6e7f8a9b
    description: Cleaned and enriched order data
    type: table
    inputContracts:
      - 53581432-6c55-4ba2-a65f-72344a91553a
```

### Management ports

Operational interfaces for observability and control.

```yaml
managementPorts:
  - name: monitoring
    content: observability
    type: rest
    url: https://grafana.example.com/d/orders
  - name: catalog
    content: discoverability
    type: rest
    url: https://catalog.example.com/products/orders
```

The `content` field must be one of: `discoverability`, `observability`, `control`, `dictionary`.

## Lineage and dbt generation

ODPS ports determine how contracts are rendered into dbt artifacts:

| Port type | dbt artifact | SQL reference |
|---|---|---|
| `inputPorts.contractId` | `sources.yml` | `{{ source() }}` |
| `outputPorts.contractId` | `schema.yml` + staging SQL | `{{ ref() }}` or `{{ source() }}` |
| Contract not in any port | `sources.yml` (default) | `{{ source() }}` |

When an `inputPort` references a contract that is also an `outputPort` of another data product, the staging SQL uses `{{ ref() }}` instead of `{{ source() }}` — recognizing it as an intermediate model rather than a raw source.

The `outputPorts.inputContracts` field defines which upstream contracts a model depends on. This determines the `FROM` clause in generated staging SQL.

## Cross-reference validation

When you run `dbt-contracts validate`, dbt-contracts checks that all `contractId` references in your product files resolve to actual ODCS contract files in `contracts/contracts/`. This can be disabled by setting `validation.cross_reference: false` in config.

## Python model

ODPS files are parsed and validated using the `OpenDataProductStandard` Pydantic model. This model is hand-rolled from the ODPS v1.0.0 specification, following the same patterns as the official ODCS Python SDK.

Shared types (`Team`, `Support`, `Description`, `CustomProperty`, `AuthoritativeDefinition`) are reused directly from the ODCS SDK to ensure consistency between contract and product definitions.

```python
from dbt_contracts.models import OpenDataProductStandard

product = OpenDataProductStandard.from_file("contracts/products/orders.odps.yaml")
print(product.name)
print(product.outputPorts[0].contractId)
```

See the [API reference](api/contracts.md) for the full model definition.

## Full example

See the [ODPS specification](https://bitol-io.github.io/open-data-product-standard/v1.0.0/) for a comprehensive example with all supported fields.
