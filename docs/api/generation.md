# Generation

Converts parsed contracts into dbt artifacts (sources, models, model SQL).

## Orchestrator

Coordinates the full generation pipeline: parse products, resolve contracts, export, generate SQL, merge YAML, and detect drift.

::: dbt_contracts.generators.orchestrator

## Exporter

Calls `datacontract-cli` to export individual contracts into dbt format.

::: dbt_contracts.generators.exporter
