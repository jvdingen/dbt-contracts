"""Tests for contract and product discovery."""

from pathlib import Path

import pytest
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.core.discovery import (
    DiscoveredContract,
    DiscoveredProduct,
    DiscoveryError,
    DiscoveryResult,
    discover,
)
from dbt_contracts.models.config import Config
from dbt_contracts.models.odps import OpenDataProductStandard

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


class TestDiscover:
    def test_returns_discovery_result(self):
        result = discover(SAMPLE_PROJECT)
        assert isinstance(result, DiscoveryResult)

    def test_loads_config(self):
        result = discover(SAMPLE_PROJECT)
        assert isinstance(result.config, Config)
        assert result.config.project_name == "sample-project"
        assert result.config.default_server_type == "snowflake"

    def test_discovers_contracts(self):
        result = discover(SAMPLE_PROJECT)
        assert len(result.contracts) == 2
        for dc in result.contracts:
            assert isinstance(dc, DiscoveredContract)
            assert isinstance(dc.contract, OpenDataContractStandard)
            assert dc.path.suffix == ".yaml"

    def test_contracts_sorted_by_filename(self):
        result = discover(SAMPLE_PROJECT)
        names = [dc.path.name for dc in result.contracts]
        assert names == sorted(names)

    def test_contract_ids_loaded(self):
        result = discover(SAMPLE_PROJECT)
        ids = {dc.contract.id for dc in result.contracts}
        assert "raw-customers" in ids
        assert "stg-orders" in ids

    def test_discovers_products(self):
        result = discover(SAMPLE_PROJECT)
        assert len(result.products) == 1
        dp = result.products[0]
        assert isinstance(dp, DiscoveredProduct)
        assert isinstance(dp.product, OpenDataProductStandard)
        assert dp.product.id == "ecommerce-product"

    def test_contract_paths_are_absolute_or_relative(self):
        result = discover(SAMPLE_PROJECT)
        for dc in result.contracts:
            assert dc.path.exists()

    def test_product_paths_exist(self):
        result = discover(SAMPLE_PROJECT)
        for dp in result.products:
            assert dp.path.exists()


class TestDiscoverMissingDir:
    def test_nonexistent_dir_raises(self):
        with pytest.raises(DiscoveryError, match="not found"):
            discover("/nonexistent/path")

    def test_missing_contracts_subdir_returns_empty(self, tmp_path):
        (tmp_path / "config.yaml").write_text("project_name: test\n")
        result = discover(tmp_path)
        assert result.contracts == []

    def test_missing_products_subdir_returns_empty(self, tmp_path):
        (tmp_path / "config.yaml").write_text("project_name: test\n")
        result = discover(tmp_path)
        assert result.products == []


class TestDiscoverDefaults:
    def test_missing_config_returns_defaults(self, tmp_path):
        (tmp_path / "contracts").mkdir()
        (tmp_path / "products").mkdir()
        result = discover(tmp_path)
        assert result.config.project_name is None
        assert result.config.default_server_type == "snowflake"

    def test_empty_contracts_dir(self, tmp_path):
        (tmp_path / "config.yaml").write_text("project_name: empty\n")
        (tmp_path / "contracts").mkdir()
        (tmp_path / "products").mkdir()
        result = discover(tmp_path)
        assert result.contracts == []
        assert result.products == []


class TestDiscoverErrors:
    def test_invalid_contract_raises(self, tmp_path):
        (tmp_path / "contracts").mkdir()
        (tmp_path / "contracts" / "bad.odcs.yaml").write_text("not: valid: yaml: [")
        with pytest.raises(DiscoveryError, match="Failed to parse"):
            discover(tmp_path)

    def test_invalid_product_raises(self, tmp_path):
        (tmp_path / "products").mkdir()
        (tmp_path / "products" / "bad.odps.yaml").write_text("not: valid: yaml: [")
        with pytest.raises(DiscoveryError, match="Failed to parse"):
            discover(tmp_path)

    def test_ignores_non_matching_files(self, tmp_path):
        (tmp_path / "contracts").mkdir()
        (tmp_path / "contracts" / "readme.md").write_text("# not a contract")
        (tmp_path / "contracts" / "data.yaml").write_text("key: value")
        result = discover(tmp_path)
        assert result.contracts == []
