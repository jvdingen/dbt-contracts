"""Pydantic models for ODPS (Open Data Product Standard) v1.0.0."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Description(BaseModel):
    """ODPS data product description."""

    model_config = ConfigDict(extra="allow")

    purpose: str | None = None
    limitations: str | None = None
    usage: str | None = None


class InputPort(BaseModel):
    """ODPS input port — data the product consumes."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    contractId: str  # noqa: N815 — matches ODPS spec field name
    description: str | None = None
    tags: list[str] | None = None
    customProperties: dict[str, str] | None = None  # noqa: N815


class InputContract(BaseModel):
    """ODPS input contract dependency — links output port to upstream contract."""

    model_config = ConfigDict(extra="allow")

    id: str
    version: str


class OutputPort(BaseModel):
    """ODPS output port — data the product produces."""

    model_config = ConfigDict(extra="allow")

    name: str
    version: str
    contractId: str  # noqa: N815 — matches ODPS spec field name
    description: str | None = None
    type: str | None = None
    tags: list[str] | None = None
    customProperties: dict[str, str] | None = None  # noqa: N815
    inputContracts: list[InputContract] | None = None  # noqa: N815


class DataProduct(BaseModel):
    """ODPS v1.0.0 data product definition."""

    model_config = ConfigDict(extra="allow")

    apiVersion: str = "v1.0.0"  # noqa: N815
    kind: str = "DataProduct"
    name: str
    id: str
    domain: str | None = None
    status: str | None = None
    tenant: str | None = None
    description: Description | None = None
    tags: list[str] | None = None
    inputPorts: list[InputPort] | None = None  # noqa: N815
    outputPorts: list[OutputPort] | None = None  # noqa: N815
