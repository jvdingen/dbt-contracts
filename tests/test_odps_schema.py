"""Tests for ODPS Pydantic model validation."""

import pytest
from pydantic import ValidationError

from dbt_contracts.odps.parser import get_input_ports, get_output_ports
from dbt_contracts.odps.schema import DataProduct


class TestSimpleProduct:
    """Parse simple product fixture — all fields correct."""

    def test_required_fields(self) -> None:
        """A DataProduct with name and id is valid."""
        product = DataProduct(name="Test", id="abc-123")
        assert product.name == "Test"
        assert product.id == "abc-123"

    def test_defaults(self) -> None:
        """Unset optional fields default to None."""
        product = DataProduct(name="Test", id="abc-123")
        assert product.apiVersion == "v1.0.0"
        assert product.kind == "DataProduct"
        assert product.domain is None
        assert product.status is None
        assert product.tenant is None
        assert product.description is None
        assert product.tags is None
        assert product.inputPorts is None
        assert product.outputPorts is None

    def test_all_fields(self) -> None:
        """A DataProduct with all fields set parses correctly."""
        product = DataProduct.model_validate(
            {
                "apiVersion": "v1.0.0",
                "kind": "DataProduct",
                "name": "Customer Data Product",
                "id": "fbe8d147-28db-4f1d-bedf-a3fe9f458427",
                "domain": "seller",
                "status": "draft",
                "tenant": "RetailCorp",
                "description": {
                    "purpose": "Enterprise view of a customer.",
                    "limitations": "No known limitations.",
                    "usage": "Check the various artefacts for their own description.",
                },
                "tags": ["customer"],
                "inputPorts": [
                    {
                        "name": "payments",
                        "version": "1.0.0",
                        "contractId": "dbb7b1eb-7628-436e-8914-2a00638ba6db",
                    }
                ],
                "outputPorts": [
                    {
                        "name": "rawtransactions",
                        "description": "Raw Transactions",
                        "type": "tables",
                        "version": "1.0.0",
                        "contractId": "c2798941-1b7e-4b03-9e0d-955b1a872b32",
                    }
                ],
            }
        )
        assert product.name == "Customer Data Product"
        assert product.domain == "seller"
        assert product.description is not None
        assert product.description.purpose == "Enterprise view of a customer."
        assert product.tags == ["customer"]
        assert product.inputPorts is not None
        assert len(product.inputPorts) == 1
        assert product.inputPorts[0].name == "payments"
        assert product.outputPorts is not None
        assert len(product.outputPorts) == 1
        assert product.outputPorts[0].name == "rawtransactions"
        assert product.outputPorts[0].type == "tables"


class TestMultiPort:
    """Parse multi-port products — correct port counts and values."""

    def test_multiple_ports(self) -> None:
        """Multiple input and output ports parse correctly."""
        product = DataProduct.model_validate(
            {
                "name": "Multi",
                "id": "multi-id",
                "inputPorts": [
                    {"name": "a", "version": "1.0.0", "contractId": "id-a"},
                    {"name": "b", "version": "1.0.0", "contractId": "id-b"},
                ],
                "outputPorts": [
                    {"name": "x", "version": "1.0.0", "contractId": "id-x"},
                    {"name": "y", "version": "2.0.0", "contractId": "id-y"},
                ],
            }
        )
        assert product.inputPorts is not None
        assert len(product.inputPorts) == 2
        assert product.inputPorts[1].name == "b"
        assert product.outputPorts is not None
        assert len(product.outputPorts) == 2
        assert product.outputPorts[1].version == "2.0.0"


class TestMinimalProduct:
    """Parse minimal product (no ports) — inputPorts/outputPorts are None."""

    def test_no_ports(self) -> None:
        """A product without ports has None for port lists."""
        product = DataProduct(name="Empty", id="empty-id")
        assert product.inputPorts is None
        assert product.outputPorts is None


class TestExtraFields:
    """Extra fields accepted (sbom, team) without error."""

    def test_extra_fields_on_product(self) -> None:
        """Unknown top-level fields are stored via extra='allow'."""
        product = DataProduct.model_validate(
            {
                "name": "Extras",
                "id": "extras-id",
                "sbom": [{"type": "external", "url": "https://example.com/sbom"}],
                "team": [{"username": "jdoe", "role": "owner"}],
            }
        )
        assert product.name == "Extras"
        assert product.model_extra is not None
        assert "sbom" in product.model_extra
        assert "team" in product.model_extra

    def test_extra_fields_on_port(self) -> None:
        """Unknown fields on ports are accepted via extra='allow'."""
        product = DataProduct.model_validate(
            {
                "name": "Extras",
                "id": "extras-id",
                "inputPorts": [
                    {
                        "name": "src",
                        "version": "1.0.0",
                        "contractId": "cid",
                        "unknownField": "hello",
                    }
                ],
            }
        )
        assert product.inputPorts is not None
        assert product.inputPorts[0].model_extra is not None
        assert product.inputPorts[0].model_extra["unknownField"] == "hello"


class TestValidationErrors:
    """Missing required fields raise ValidationError."""

    def test_missing_name(self) -> None:
        """Omitting name raises ValidationError."""
        with pytest.raises(ValidationError):
            DataProduct.model_validate({"id": "some-id"})

    def test_missing_id(self) -> None:
        """Omitting id raises ValidationError."""
        with pytest.raises(ValidationError):
            DataProduct.model_validate({"name": "Some Name"})

    def test_missing_port_required_fields(self) -> None:
        """Omitting required port fields raises ValidationError."""
        with pytest.raises(ValidationError):
            DataProduct.model_validate(
                {
                    "name": "Bad",
                    "id": "bad-id",
                    "inputPorts": [{"name": "missing-version-and-contract"}],
                }
            )


class TestPortHelpers:
    """get_input_ports() / get_output_ports() helpers work."""

    def test_get_input_ports(self) -> None:
        """get_input_ports returns the input port list."""
        product = DataProduct.model_validate(
            {
                "name": "P",
                "id": "pid",
                "inputPorts": [{"name": "a", "version": "1.0", "contractId": "cid"}],
            }
        )
        ports = get_input_ports(product)
        assert len(ports) == 1
        assert ports[0].name == "a"

    def test_get_output_ports(self) -> None:
        """get_output_ports returns the output port list."""
        product = DataProduct.model_validate(
            {
                "name": "P",
                "id": "pid",
                "outputPorts": [{"name": "b", "version": "2.0", "contractId": "cid"}],
            }
        )
        ports = get_output_ports(product)
        assert len(ports) == 1
        assert ports[0].name == "b"

    def test_get_ports_none(self) -> None:
        """Helpers return empty list when ports are None."""
        product = DataProduct(name="Empty", id="eid")
        assert get_input_ports(product) == []
        assert get_output_ports(product) == []
