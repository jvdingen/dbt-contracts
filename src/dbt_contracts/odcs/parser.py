"""Load and parse ODCS YAML files via the open-data-contract-standard library."""

from __future__ import annotations

from pathlib import Path

from open_data_contract_standard.model import OpenDataContractStandard


def load_odcs(file_path: Path) -> OpenDataContractStandard:
    """Load and parse an ODCS YAML file into an OpenDataContractStandard model."""
    return OpenDataContractStandard.from_file(str(file_path))


def load_odcs_by_id(contract_id: str, odcs_dir: Path) -> OpenDataContractStandard:
    """Load an ODCS contract by its unique id field.

    Searches odcs_dir recursively for .odcs.yaml files whose id matches contract_id.

    Raises:
        FileNotFoundError: If no contract with the given id is found.
    """
    for path in odcs_dir.glob("**/*.odcs.yaml"):
        contract = load_odcs(path)
        if contract.id == contract_id:
            return contract
    msg = f"No ODCS contract found with id '{contract_id}' in {odcs_dir}"
    raise FileNotFoundError(msg)
