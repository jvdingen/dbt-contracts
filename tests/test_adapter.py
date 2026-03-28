"""Tests for the adapter layer wrapping datacontract-cli."""

from pathlib import Path

import pytest
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.core.adapter import (
    GenerationResult,
    LintResult,
    _build_lineage,
    lint,
    render,
)
from dbt_contracts.models.odps import OpenDataProductStandard

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def customers_contract():
    return OpenDataContractStandard.from_file(str(FIXTURES / "customers.odcs.yaml"))


@pytest.fixture
def orders_contract():
    return OpenDataContractStandard.from_file(str(FIXTURES / "orders.odcs.yaml"))


@pytest.fixture
def ecommerce_product():
    return OpenDataProductStandard.from_file(str(FIXTURES / "ecommerce.odps.yaml"))


class TestLint:
    def test_valid_contract(self, customers_contract):
        result = lint(customers_contract)
        assert isinstance(result, LintResult)
        assert result.passed is True
        assert result.errors == []

    def test_invalid_contract(self):
        contract = OpenDataContractStandard.from_string(
            "kind: DataContract\napiVersion: v3.1.0\nid: bad\n"
        )
        result = lint(contract)
        assert result.passed is False
        assert len(result.errors) > 0


class TestBuildLineage:
    def test_input_port_is_source(self, customers_contract, ecommerce_product):
        contracts_by_id = {customers_contract.id: customers_contract}
        lineage = _build_lineage(contracts_by_id, [ecommerce_product])
        assert lineage["raw-customers"] == "source"

    def test_output_port_is_model(self, orders_contract, ecommerce_product):
        contracts_by_id = {orders_contract.id: orders_contract}
        lineage = _build_lineage(contracts_by_id, [ecommerce_product])
        assert lineage["stg-orders"] == "model"

    def test_contract_not_in_any_port_defaults_to_source(self):
        contract = OpenDataContractStandard.model_validate(
            {"id": "orphan", "kind": "DataContract", "apiVersion": "v3.1.0"}
        )
        lineage = _build_lineage({"orphan": contract}, [])
        assert lineage["orphan"] == "source"

    def test_input_port_that_is_output_of_another_odps_is_ref(
        self, customers_contract, orders_contract
    ):
        """When a contract is an inputPort of one product but an outputPort
        of another, it should be classified as ref."""
        upstream_product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: upstream-product
version: 1.0.0
status: active
name: Upstream Product
outputPorts:
  - name: customers-output
    contractId: raw-customers
"""
        )
        downstream_product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: downstream-product
version: 1.0.0
status: active
name: Downstream Product
inputPorts:
  - name: customers-input
    contractId: raw-customers
outputPorts:
  - name: orders-output
    contractId: stg-orders
"""
        )
        contracts_by_id = {
            customers_contract.id: customers_contract,
            orders_contract.id: orders_contract,
        }
        lineage = _build_lineage(
            contracts_by_id, [upstream_product, downstream_product]
        )
        assert lineage["raw-customers"] == "model"
        assert lineage["stg-orders"] == "model"


class TestRender:
    def test_returns_generation_result(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        assert isinstance(result, GenerationResult)

    def test_sources_contain_upstream_contract(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        assert len(result.sources) == 1
        source = result.sources[0]
        assert source["version"] == 2
        assert source["sources"][0]["name"] == "raw-customers"
        assert source["sources"][0]["database"] == "RAW"
        assert source["sources"][0]["schema"] == "PUBLIC"

    def test_sources_have_tables_and_columns(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        source = result.sources[0]
        tables = source["sources"][0]["tables"]
        assert len(tables) == 1
        assert tables[0]["name"] == "raw_customers"
        columns = tables[0]["columns"]
        column_names = [c["name"] for c in columns]
        assert "customer_id" in column_names
        assert "email" in column_names

    def test_models_contain_downstream_contract(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        assert len(result.models) == 1
        model = result.models[0]
        assert model["version"] == 2
        assert model["models"][0]["name"] == "stg_orders"

    def test_model_has_columns_and_config(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        model = result.models[0]["models"][0]
        assert "config" in model
        column_names = [c["name"] for c in model["columns"]]
        assert "order_id" in column_names
        assert "customer_id" in column_names
        assert "amount" in column_names
        assert "created_at" in column_names

    def test_staging_sql_generated_for_model(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        result = render([customers_contract, orders_contract], [ecommerce_product])
        assert "stg_orders" in result.staging_sql
        sql = result.staging_sql["stg_orders"]
        assert "order_id" in sql
        assert "customer_id" in sql

    def test_staging_sql_references_upstream_source(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        """Model SQL should reference its upstream input contract as source."""
        result = render([customers_contract, orders_contract], [ecommerce_product])
        sql = result.staging_sql["stg_orders"]
        assert "{{ source('raw-customers', 'raw_customers') }}" in sql

    def test_server_type_from_contract(
        self, customers_contract, orders_contract, ecommerce_product
    ):
        """Server type should be resolved from the contract, not the default."""
        result = render(
            [customers_contract, orders_contract],
            [ecommerce_product],
            default_server_type="postgres",
        )
        # Contracts specify snowflake, so output should use snowflake types
        model = result.models[0]["models"][0]
        columns_by_name = {c["name"]: c for c in model["columns"]}
        assert columns_by_name["order_id"]["data_type"] == "NUMBER"

    def test_fallback_to_default_server_type(self, ecommerce_product):
        """Contract without servers should use the default server type."""
        contract = OpenDataContractStandard.model_validate(
            {
                "id": "no-server",
                "kind": "DataContract",
                "apiVersion": "v3.1.0",
                "version": "1.0.0",
                "status": "active",
                "schema": [
                    {
                        "name": "test_table",
                        "properties": [
                            {"name": "col1", "logicalType": "string"},
                        ],
                    }
                ],
            }
        )
        result = render([contract], [], default_server_type="postgres")
        assert len(result.sources) == 1

    def test_ref_replaces_source_in_sql(self, customers_contract, orders_contract):
        """When an input contract is also an output of another ODPS,
        staging SQL should use ref() instead of source()."""
        upstream_product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: upstream-product
version: 1.0.0
status: active
name: Upstream Product
outputPorts:
  - name: customers-output
    contractId: raw-customers
"""
        )
        downstream_product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: downstream-product
version: 1.0.0
status: active
name: Downstream Product
inputPorts:
  - name: customers-input
    contractId: raw-customers
outputPorts:
  - name: orders-output
    contractId: stg-orders
    inputContracts:
      - raw-customers
"""
        )
        result = render(
            [customers_contract, orders_contract],
            [upstream_product, downstream_product],
        )
        sql = result.staging_sql["stg_orders"]
        assert "{{ ref('raw_customers') }}" in sql
        assert "source('raw-customers'" not in sql
