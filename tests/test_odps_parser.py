"""Tests for ODPS YAML file loading."""

from pathlib import Path

import pytest

from dbt_contracts.odps.parser import load_odps
from dbt_contracts.odps.schema import DataProduct

FIXTURES = Path(__file__).parent / "fixtures" / "odps"


class TestLoadOdps:
    """load_odps() from fixture path returns valid DataProduct."""

    def test_load_simple_product(self) -> None:
        """Loading simple_product.odps.yaml returns correct DataProduct."""
        product = load_odps(FIXTURES / "simple_product.odps.yaml")
        assert isinstance(product, DataProduct)
        assert product.name == "Customer Data Product"
        assert product.id == "fbe8d147-28db-4f1d-bedf-a3fe9f458427"
        assert product.domain == "seller"
        assert product.inputPorts is not None
        assert len(product.inputPorts) == 1
        assert product.outputPorts is not None
        assert len(product.outputPorts) == 1

    def test_load_multi_port_product(self) -> None:
        """Loading multi_port_product.odps.yaml returns correct port counts."""
        product = load_odps(FIXTURES / "multi_port_product.odps.yaml")
        assert product.inputPorts is not None
        assert len(product.inputPorts) == 2
        assert product.outputPorts is not None
        assert len(product.outputPorts) == 2

    def test_load_minimal_product(self) -> None:
        """Loading minimal_product.odps.yaml returns product with no ports."""
        product = load_odps(FIXTURES / "minimal_product.odps.yaml")
        assert product.name == "Empty Product"
        assert product.inputPorts is None
        assert product.outputPorts is None

    def test_load_with_extras(self) -> None:
        """Loading with_extras.odps.yaml accepts extra fields without error."""
        product = load_odps(FIXTURES / "with_extras.odps.yaml")
        assert product.name == "Product With Extras"
        assert product.model_extra is not None
        assert "sbom" in product.model_extra
        assert "team" in product.model_extra

    def test_nonexistent_file(self) -> None:
        """Loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_odps(FIXTURES / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Loading a file with invalid content raises a validation error."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("just a string, not a mapping")
        with pytest.raises(Exception):  # noqa: B017
            load_odps(bad_file)
