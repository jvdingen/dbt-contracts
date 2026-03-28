# Generation

## Adapter Layer

The adapter module wraps `datacontract-cli` exporters and adds lineage-aware rendering from ODPS products.

::: dbt_contracts.core.adapter
    options:
      members:
        - lint
        - render
        - LintResult
        - GenerationResult
