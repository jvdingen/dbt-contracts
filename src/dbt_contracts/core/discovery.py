"""Contract and product discovery from the /contracts directory.

Scans for ODCS contract files, ODPS product files, and the config file,
returning structured results ready for validation and rendering.
"""

from __future__ import annotations

from pathlib import Path

import pydantic as pyd
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.models.config import Config
from dbt_contracts.models.odps import OpenDataProductStandard


class DiscoveredContract(pyd.BaseModel):
    """An ODCS contract discovered from the filesystem."""

    path: Path
    contract: OpenDataContractStandard

    model_config = pyd.ConfigDict(arbitrary_types_allowed=True)


class DiscoveredProduct(pyd.BaseModel):
    """An ODPS product discovered from the filesystem."""

    path: Path
    product: OpenDataProductStandard

    model_config = pyd.ConfigDict(arbitrary_types_allowed=True)


class DiscoveryResult(pyd.BaseModel):
    """Result of scanning a contracts directory."""

    config: Config
    contracts: list[DiscoveredContract] = pyd.Field(default_factory=list)
    products: list[DiscoveredProduct] = pyd.Field(default_factory=list)

    model_config = pyd.ConfigDict(arbitrary_types_allowed=True)


class DiscoveryError(Exception):
    """Raised when contract discovery encounters a problem."""


def discover(contracts_dir: str | Path) -> DiscoveryResult:
    """Scan a contracts directory and load all contracts, products, and config.

    Expects the following structure::

        contracts_dir/
        ├── config.yaml
        ├── contracts/*.odcs.yaml
        └── products/*.odps.yaml

    Args:
        contracts_dir: Path to the contracts directory.

    Returns:
        DiscoveryResult with parsed config, contracts, and products.

    Raises:
        DiscoveryError: If the directory does not exist or a file fails to parse.
    """
    base = Path(contracts_dir)
    if not base.is_dir():
        raise DiscoveryError(f"Contracts directory not found: {base}")

    config = _load_config(base)
    contracts = _load_contracts(base / "contracts")
    products = _load_products(base / "products")

    return DiscoveryResult(
        config=config,
        contracts=contracts,
        products=products,
    )


def _load_config(base: Path) -> Config:
    """Load config.yaml from the contracts directory, or return defaults."""
    config_path = base / "config.yaml"
    if config_path.exists():
        return Config.from_file(str(config_path))
    return Config()


def _load_contracts(contracts_path: Path) -> list[DiscoveredContract]:
    """Load all .odcs.yaml files from the contracts subdirectory."""
    if not contracts_path.is_dir():
        return []

    results = []
    for path in sorted(contracts_path.glob("*.odcs.yaml")):
        try:
            contract = OpenDataContractStandard.from_file(str(path))
        except Exception as e:
            raise DiscoveryError(f"Failed to parse {path}: {e}") from e
        results.append(DiscoveredContract(path=path, contract=contract))
    return results


def _load_products(products_path: Path) -> list[DiscoveredProduct]:
    """Load all .odps.yaml files from the products subdirectory."""
    if not products_path.is_dir():
        return []

    results = []
    for path in sorted(products_path.glob("*.odps.yaml")):
        try:
            product = OpenDataProductStandard.from_file(str(path))
        except Exception as e:
            raise DiscoveryError(f"Failed to parse {path}: {e}") from e
        results.append(DiscoveredProduct(path=path, product=product))
    return results
