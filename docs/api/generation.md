# Generation

Converts parsed contracts into dbt artifacts (sources, models, model SQL).

## Orchestrator

Coordinates the full generation pipeline: parse products, resolve contracts, export, generate SQL, merge YAML, and detect drift.

::: dbt_contracts.generators.orchestrator

## Exporter

Calls `datacontract-cli` to export individual contracts into dbt format.

::: dbt_contracts.generators.exporter

## Quality

Converts ODCS quality rules to dbt test entries and injects them into schema YAML.

::: dbt_contracts.generators.quality

## Metadata

Propagates contract/product metadata (tags, descriptions, owner, domain, column meta) into schema YAML.

::: dbt_contracts.generators.metadata
