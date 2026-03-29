"""Import existing dbt YAML files and generate ODCS contract stubs."""

from __future__ import annotations

from pathlib import Path

import pydantic as pyd
import yaml

from dbt_contracts.core.generator import to_yaml


class ImportedContract(pyd.BaseModel):
    """A contract stub generated from a dbt YAML file."""

    path: Path
    content: str


class ImportResult(pyd.BaseModel):
    """Result of importing dbt YAML files."""

    contracts: list[ImportedContract] = pyd.Field(default_factory=list)


def import_dbt(
    schema_paths: list[Path],
    output_dir: Path,
    server_type: str = "snowflake",
    dry_run: bool = False,
) -> ImportResult:
    """Parse dbt schema YAML files and generate ODCS contract stubs.

    Args:
        schema_paths: Paths to dbt schema.yml files.
        output_dir: Directory to write generated contract files.
        server_type: Default server type for contracts.
        dry_run: Preview without writing files.

    Returns:
        ImportResult with generated contract stubs.
    """
    contracts: list[ImportedContract] = []

    for schema_path in schema_paths:
        data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        if not data:
            continue

        for source in data.get("sources", []):
            contract = _source_to_contract(source, server_type)
            name = source.get("name", "source")
            path = output_dir / f"{name}.odcs.yaml"
            content = to_yaml(contract)
            contracts.append(ImportedContract(path=path, content=content))

        for model in data.get("models", []):
            contract = _model_to_contract(model, server_type)
            name = model.get("name", "model")
            path = output_dir / f"{name}.odcs.yaml"
            content = to_yaml(contract)
            contracts.append(ImportedContract(path=path, content=content))

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        for c in contracts:
            c.path.parent.mkdir(parents=True, exist_ok=True)
            c.path.write_text(c.content, encoding="utf-8")

    return ImportResult(contracts=contracts)


def _source_to_contract(source: dict, server_type: str) -> dict:
    """Convert a dbt source definition to an ODCS contract dict."""
    name = source.get("name", "source")
    database = source.get("database", "")
    schema_name = source.get("schema", "")

    tables = []
    for table in source.get("tables", []):
        properties = []
        for col in table.get("columns", []):
            prop = {"name": col["name"]}
            if col.get("description"):
                prop["description"] = col["description"]
            if col.get("data_type"):
                prop["physicalType"] = col["data_type"]
            tests = col.get("data_tests", [])
            if "not_null" in tests:
                prop["required"] = True
            if "unique" in tests:
                prop["unique"] = True
            properties.append(prop)

        table_dict: dict = {"name": table.get("name", name)}
        if table.get("description"):
            table_dict["description"] = table["description"]
        table_dict["physicalType"] = "table"
        if properties:
            table_dict["properties"] = properties
        tables.append(table_dict)

    contract: dict = {
        "kind": "DataContract",
        "apiVersion": "v3.1.0",
        "id": name,
        "version": "1.0.0",
        "status": "draft",
        "name": name,
    }

    server: dict = {"server": "production", "type": server_type}
    if database:
        server["database"] = database
    if schema_name:
        server["schema"] = schema_name
    contract["servers"] = [server]

    if tables:
        contract["schema"] = tables

    return contract


def _model_to_contract(model: dict, server_type: str) -> dict:
    """Convert a dbt model definition to an ODCS contract dict."""
    name = model.get("name", "model")

    properties = []
    for col in model.get("columns", []):
        prop: dict = {"name": col["name"]}
        if col.get("description"):
            prop["description"] = col["description"]
        if col.get("data_type"):
            prop["physicalType"] = col["data_type"]
        constraints = col.get("constraints", [])
        for c in constraints:
            if c.get("type") == "not_null":
                prop["required"] = True
            if c.get("type") == "unique":
                prop["unique"] = True
        tests = col.get("data_tests", [])
        if "not_null" in tests:
            prop["required"] = True
        if "unique" in tests:
            prop["unique"] = True
        properties.append(prop)

    schema_obj: dict = {"name": name}
    if model.get("description"):
        schema_obj["description"] = model["description"]
    schema_obj["physicalType"] = "table"
    if properties:
        schema_obj["properties"] = properties

    contract: dict = {
        "kind": "DataContract",
        "apiVersion": "v3.1.0",
        "id": name,
        "version": "1.0.0",
        "status": "draft",
        "name": name,
        "servers": [{"server": "production", "type": server_type}],
        "schema": [schema_obj],
    }

    return contract
