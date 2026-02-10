"""Load and parse ODPS YAML files into Pydantic models."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import DataProduct, InputPort, OutputPort


def load_odps(file_path: Path) -> DataProduct:
    """Load and parse an ODPS YAML file into a DataProduct."""
    raw = yaml.safe_load(file_path.read_text())
    return DataProduct.model_validate(raw)


def get_input_ports(product: DataProduct) -> list[InputPort]:
    """Extract all input ports from a data product."""
    return product.inputPorts or []


def get_output_ports(product: DataProduct) -> list[OutputPort]:
    """Extract all output ports from a data product."""
    return product.outputPorts or []
