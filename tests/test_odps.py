"""Tests for the ODPS models."""

import pytest
from open_data_contract_standard.model import (
    AuthoritativeDefinition as OdcsAuthoritativeDefinition,
)
from open_data_contract_standard.model import CustomProperty as OdcsCustomProperty
from open_data_contract_standard.model import Description as OdcsDescription
from open_data_contract_standard.model import Support as OdcsSupport
from open_data_contract_standard.model import Team as OdcsTeam
from pydantic import ValidationError

from dbt_contracts.models.odps import (
    InputPort,
    ManagementPort,
    OpenDataProductStandard,
    OutputPort,
    Sbom,
)

MINIMAL_ODPS = {
    "kind": "DataProduct",
    "apiVersion": "v1.0.0",
    "id": "a8f5f167-e42a-4b5c-8c9d-2d3e4f5a6b7c",
    "status": "active",
}

FULL_ODPS_YAML = """\
kind: DataProduct
apiVersion: v1.0.0
id: a8f5f167-e42a-4b5c-8c9d-2d3e4f5a6b7c
name: Order Analytics
domain: commerce
version: 1.0.0
status: active

description:
  purpose: Provide analytics-ready order data
  limitations: Only completed orders
  usage: Connect via Snowflake output port

tags:
  - analytics
  - commerce

inputPorts:
  - name: raw-orders
    version: 1.0.0
    contractId: 53581432-6c55-4ba2-a65f-72344a91553a

outputPorts:
  - name: analytics-orders
    version: 1.0.0
    contractId: e4f5a6b7-c8d9-0e1f-2a3b-4c5d6e7f8a9b
    description: Cleaned and enriched order data
    type: table
    sbom:
      type: CycloneDX
      url: https://example.com/sbom.json
    inputContracts:
      - 53581432-6c55-4ba2-a65f-72344a91553a

managementPorts:
  - name: monitoring
    content: observability
    type: rest
    url: https://grafana.example.com/d/orders
  - name: catalog
    content: discoverability

team:
  name: Commerce Data Team
  members:
    - username: jsmith
      role: Product Owner
    - username: ajones
      role: Data Engineer

support:
  - channel: slack
    url: https://myorg.slack.com/archives/C123456
    tool: Slack

customProperties:
  - property: costCenter
    value: CC-1234

productCreatedTs: "2025-01-15T10:30:00Z"
"""


class TestOpenDataProductStandard:
    def test_minimal(self):
        product = OpenDataProductStandard(**MINIMAL_ODPS)
        assert product.kind == "DataProduct"
        assert product.apiVersion == "v1.0.0"
        assert product.id == "a8f5f167-e42a-4b5c-8c9d-2d3e4f5a6b7c"
        assert product.status == "active"

    def test_full_example(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert product.name == "Order Analytics"
        assert product.domain == "commerce"
        assert product.description.purpose == "Provide analytics-ready order data"
        assert len(product.inputPorts) == 1
        assert len(product.outputPorts) == 1
        assert len(product.managementPorts) == 2
        assert len(product.team.members) == 2
        assert len(product.support) == 1
        assert len(product.customProperties) == 1
        assert product.productCreatedTs == "2025-01-15T10:30:00Z"

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            OpenDataProductStandard(**MINIMAL_ODPS, unknown_field="bad")

    def test_empty_construction(self):
        product = OpenDataProductStandard()
        assert product.kind is None
        assert product.inputPorts is None


class TestFromString:
    def test_parse_yaml(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert product.kind == "DataProduct"
        assert product.tags == ["analytics", "commerce"]

    def test_empty_string(self):
        product = OpenDataProductStandard.from_string("")
        assert product.kind is None


class TestFromFile:
    def test_load_from_file(self, tmp_path):
        path = tmp_path / "product.odps.yaml"
        path.write_text(FULL_ODPS_YAML)
        product = OpenDataProductStandard.from_file(str(path))
        assert product.name == "Order Analytics"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            OpenDataProductStandard.from_file("/nonexistent/product.odps.yaml")


class TestToYaml:
    def test_roundtrip(self):
        original = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        yaml_str = original.to_yaml()
        restored = OpenDataProductStandard.from_string(yaml_str)
        assert restored.name == original.name
        assert restored.kind == original.kind
        assert restored.inputPorts[0].contractId == (original.inputPorts[0].contractId)
        assert restored.outputPorts[0].sbom.type == (original.outputPorts[0].sbom.type)


class TestInputPort:
    def test_all_fields(self):
        port = InputPort(
            name="raw-data",
            version="1.0.0",
            contractId="some-uuid",
            tags=["source"],
            customProperties=[{"property": "key", "value": "val"}],
            authoritativeDefinitions=[{"url": "https://example.com"}],
        )
        assert port.name == "raw-data"
        assert port.contractId == "some-uuid"
        assert len(port.customProperties) == 1
        assert len(port.authoritativeDefinitions) == 1


class TestOutputPort:
    def test_with_sbom(self):
        port = OutputPort(
            name="analytics",
            version="1.0.0",
            sbom=Sbom(type="CycloneDX", url="https://example.com/sbom.json"),
            inputContracts=["uuid-1", "uuid-2"],
        )
        assert port.sbom.type == "CycloneDX"
        assert len(port.inputContracts) == 2


class TestManagementPort:
    def test_all_fields(self):
        port = ManagementPort(
            name="monitoring",
            content="observability",
            type="rest",
            url="https://grafana.example.com",
            channel="ops-channel",
            description="Pipeline health dashboard",
        )
        assert port.content == "observability"
        assert port.type == "rest"


class TestSharedTypes:
    def test_description_is_odcs_type(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert isinstance(product.description, OdcsDescription)

    def test_team_is_odcs_type(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert isinstance(product.team, OdcsTeam)

    def test_support_is_odcs_type(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert isinstance(product.support[0], OdcsSupport)

    def test_custom_property_is_odcs_type(self):
        product = OpenDataProductStandard.from_string(FULL_ODPS_YAML)
        assert isinstance(product.customProperties[0], OdcsCustomProperty)

    def test_authoritative_definition_type(self):
        port = InputPort(
            authoritativeDefinitions=[{"url": "https://example.com"}],
        )
        assert isinstance(port.authoritativeDefinitions[0], OdcsAuthoritativeDefinition)
