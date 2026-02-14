"""Database adapter profile templates for dbt project scaffolding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterInfo:
    """Display label and profiles.yml template for a dbt adapter."""

    label: str
    profile: str


ADAPTERS: dict[str, AdapterInfo] = {
    "duckdb": AdapterInfo(
        label="DuckDB (local, zero-config)",
        profile="""\
{project_name}:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{project_name}.duckdb"
""",
    ),
    "postgres": AdapterInfo(
        label="PostgreSQL",
        profile="""\
{project_name}:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: your_user
      password: your_password
      dbname: your_database
      schema: public
      threads: 4
""",
    ),
    "snowflake": AdapterInfo(
        label="Snowflake",
        profile="""\
{project_name}:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_account
      user: your_user
      password: your_password
      role: your_role
      database: your_database
      warehouse: your_warehouse
      schema: public
      threads: 4
""",
    ),
    "bigquery": AdapterInfo(
        label="BigQuery",
        profile="""\
{project_name}:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: your-gcp-project
      dataset: your_dataset
      threads: 4
""",
    ),
}
