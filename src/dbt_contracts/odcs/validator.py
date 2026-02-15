"""Validate ODCS contracts via datacontract-cli lint and test."""

from __future__ import annotations

from pathlib import Path

from datacontract.data_contract import DataContract
from datacontract.model.run import ResultEnum


def _format_check_error(check: object) -> str:
    """Format a failed check into a human-readable error message."""
    name = getattr(check, "name", None) or "unknown"
    reason = getattr(check, "reason", None) or "no reason given"
    return f"{name}: {reason}"


def _run_validation(contract_path: Path, method_name: str) -> tuple[bool, list[str]]:
    """Run a datacontract-cli validation method and collect errors."""
    dc = DataContract(data_contract_file=str(contract_path))
    result = getattr(dc, method_name)()
    errors = [_format_check_error(c) for c in (result.checks or []) if c.result != ResultEnum.passed]
    return result.has_passed(), errors


def lint_contract(contract_path: Path) -> tuple[bool, list[str]]:
    """Validate ODCS contract YAML structure offline (no database needed).

    Returns:
        A tuple of (success, errors) where success is True if all checks passed
        and errors is a list of human-readable messages for any failed checks.
    """
    return _run_validation(contract_path, "lint")


def test_contract(contract_path: Path) -> tuple[bool, list[str]]:
    """Test ODCS contract against live data (requires server configuration).

    Returns:
        A tuple of (success, errors) where success is True if all checks passed
        and errors is a list of human-readable messages for any failed checks.
    """
    return _run_validation(contract_path, "test")
