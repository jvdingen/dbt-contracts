# Generation

Converts parsed contracts into dbt artifacts (sources, models, staging SQL).

## Orchestrator

Coordinates the full generation pipeline: parse products, resolve contracts, export, and post-process.

::: dbt_contracts.generators.orchestrator

## Exporter

Calls `datacontract-cli` to export individual contracts into dbt format.

::: dbt_contracts.generators.exporter

## Post-processing

Merges per-contract exports, renames sources to match port names, and rewires `source()` references using `inputContracts` lineage.

::: dbt_contracts.generators.postprocess
