"""Pydantic models for the Open Data Product Standard (ODPS) v1.0.0."""

from __future__ import annotations

import pydantic as pyd
import yaml
from open_data_contract_standard.model import (
    AuthoritativeDefinition,
    CustomProperty,
    Description,
    Support,
    Team,
)


class Sbom(pyd.BaseModel):
    """Software Bill of Materials for an output port."""

    type: str | None = None
    url: str | None = None


class InputPort(pyd.BaseModel):
    """An input port describing a data ingestion source."""

    name: str | None = None
    version: str | None = None
    contractId: str | None = None
    tags: list[str] | None = None
    customProperties: list[CustomProperty] | None = None
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = None


class OutputPort(pyd.BaseModel):
    """An output port describing exposed data."""

    name: str | None = None
    version: str | None = None
    contractId: str | None = None
    description: str | None = None
    type: str | None = None
    sbom: Sbom | None = None
    inputContracts: list[str] | None = None
    tags: list[str] | None = None
    customProperties: list[CustomProperty] | None = None
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = None


class ManagementPort(pyd.BaseModel):
    """A management port for operational interfaces."""

    name: str | None = None
    content: str | None = None
    type: str | None = None
    url: str | None = None
    channel: str | None = None
    description: str | None = None


class OpenDataProductStandard(pyd.BaseModel):
    """Root model for an ODPS v1.0.0 data product definition.

    Loaded from ``.odps.yaml`` files.
    """

    model_config = pyd.ConfigDict(extra="forbid")

    kind: str | None = None
    apiVersion: str | None = None
    id: str | None = None
    status: str | None = None
    name: str | None = None
    version: str | None = None
    domain: str | None = None
    tenant: str | None = None
    description: Description | None = None
    tags: list[str] | None = None
    inputPorts: list[InputPort] | None = None
    outputPorts: list[OutputPort] | None = None
    managementPorts: list[ManagementPort] | None = None
    support: list[Support] | None = None
    team: Team | None = None
    customProperties: list[CustomProperty] | None = None
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = None
    productCreatedTs: str | None = None

    @classmethod
    def from_file(cls, file_path: str) -> OpenDataProductStandard:
        """Load a data product definition from a YAML file."""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return cls.from_string(content)

    @classmethod
    def from_string(cls, data_product_str: str) -> OpenDataProductStandard:
        """Load a data product definition from a YAML string."""
        data = yaml.safe_load(data_product_str) or {}
        return cls(**data)

    def to_yaml(self) -> str:
        """Serialize the data product definition to a YAML string."""
        return yaml.dump(
            self.model_dump(exclude_defaults=True, exclude_none=True, by_alias=True),
            sort_keys=False,
            allow_unicode=True,
        )
