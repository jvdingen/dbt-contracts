"""Core logic for contract processing, validation, and dbt generation."""

from dbt_contracts.core.adapter import GenerationResult, LintResult, lint, render
from dbt_contracts.core.discovery import (
    DiscoveredContract,
    DiscoveredProduct,
    DiscoveryError,
    DiscoveryResult,
    discover,
)
from dbt_contracts.core.validation import ValidationIssue, ValidationResult, validate

__all__ = [
    "DiscoveredContract",
    "DiscoveredProduct",
    "DiscoveryError",
    "DiscoveryResult",
    "GenerationResult",
    "LintResult",
    "discover",
    "ValidationIssue",
    "ValidationResult",
    "lint",
    "render",
    "validate",
]
