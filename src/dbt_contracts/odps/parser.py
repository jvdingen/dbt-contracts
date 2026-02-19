"""Load and parse ODPS YAML files into Pydantic models."""

from __future__ import annotations

from pathlib import Path

import yaml

from .schema import DataProduct


def load_odps(file_path: Path) -> DataProduct:
    """Load and parse an ODPS YAML file into a DataProduct."""
    raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    return DataProduct.model_validate(raw)
