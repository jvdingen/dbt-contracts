"""Tests for ODCS contract validation via datacontract-cli."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from datacontract.model.run import Check, ResultEnum, Run

from dbt_contracts.odcs import validator

FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


def _make_run(checks: list[Check]) -> Run:
    """Create a Run object with the given checks for mocking."""
    return Run(
        runId=uuid.uuid4(),
        timestampStart=datetime.now(),
        timestampEnd=datetime.now(),
        checks=checks,
        logs=[],
    )


class TestLintContract:
    """lint_contract() validates ODCS YAML structure offline."""

    def test_valid_contract_passes(self) -> None:
        """Linting simple_table.odcs.yaml succeeds with no errors."""
        passed, errors = validator.lint_contract(FIXTURES / "simple_table.odcs.yaml")
        assert passed is True
        assert errors == []

    def test_minimal_contract_passes(self) -> None:
        """Linting minimal_contract.odcs.yaml succeeds."""
        passed, errors = validator.lint_contract(FIXTURES / "minimal_contract.odcs.yaml")
        assert passed is True
        assert errors == []

    def test_invalid_contract_fails(self) -> None:
        """Linting invalid_contract.odcs.yaml fails with error messages."""
        passed, errors = validator.lint_contract(FIXTURES / "invalid_contract.odcs.yaml")
        assert passed is False
        assert len(errors) > 0

    def test_nonexistent_file_fails(self) -> None:
        """Linting a nonexistent file returns failure with error message."""
        passed, errors = validator.lint_contract(FIXTURES / "nonexistent.yaml")
        assert passed is False
        assert len(errors) > 0


class TestTestContract:
    """test_contract() is tested with mocked DataContract since it needs a live database."""

    @patch("dbt_contracts.odcs.validator.DataContract")
    def test_all_checks_pass(self, mock_dc_cls: MagicMock) -> None:
        """When all checks pass, test_contract returns (True, [])."""
        checks = [Check(type="general", name="schema", result=ResultEnum.passed)]
        mock_dc_cls.return_value.test.return_value = _make_run(checks)

        passed, errors = validator.test_contract(FIXTURES / "simple_table.odcs.yaml")
        assert passed is True
        assert errors == []

    @patch("dbt_contracts.odcs.validator.DataContract")
    def test_failed_checks(self, mock_dc_cls: MagicMock) -> None:
        """When checks fail, test_contract returns (False, [error messages])."""
        checks = [
            Check(type="general", name="schema", result=ResultEnum.passed),
            Check(type="general", name="row_count", result=ResultEnum.failed, reason="expected 100, got 0"),
        ]
        mock_dc_cls.return_value.test.return_value = _make_run(checks)

        passed, errors = validator.test_contract(FIXTURES / "simple_table.odcs.yaml")
        assert passed is False
        assert len(errors) == 1
        assert "row_count" in errors[0]
        assert "expected 100, got 0" in errors[0]

    @patch("dbt_contracts.odcs.validator.DataContract")
    def test_all_checks_fail(self, mock_dc_cls: MagicMock) -> None:
        """When all checks fail, all errors are returned."""
        checks = [
            Check(type="general", name="check1", result=ResultEnum.failed, reason="reason1"),
            Check(type="general", name="check2", result=ResultEnum.failed, reason="reason2"),
        ]
        mock_dc_cls.return_value.test.return_value = _make_run(checks)

        passed, errors = validator.test_contract(FIXTURES / "simple_table.odcs.yaml")
        assert passed is False
        assert len(errors) == 2
