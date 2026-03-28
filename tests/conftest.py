"""Shared test fixtures for dbt-contracts."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()
