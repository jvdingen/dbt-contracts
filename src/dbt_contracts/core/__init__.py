"""Core logic for contract processing, validation, and dbt generation."""

from dbt_contracts.core.adapter import GenerationResult, LintResult, lint, render
from dbt_contracts.core.differ import DiffResult, FileDiff, FileStatus, diff
from dbt_contracts.core.discovery import (
    DiscoveredContract,
    DiscoveredProduct,
    DiscoveryError,
    DiscoveryResult,
    discover,
)
from dbt_contracts.core.generator import (
    GeneratedFile,
    GenerateResult,
    generate,
    to_yaml,
)
from dbt_contracts.core.importer import ImportedContract, ImportResult, import_dbt
from dbt_contracts.core.init import InitResult, init
from dbt_contracts.core.validation import ValidationIssue, ValidationResult, validate

__all__ = [
    "DiffResult",
    "DiscoveredContract",
    "DiscoveredProduct",
    "DiscoveryError",
    "DiscoveryResult",
    "FileDiff",
    "FileStatus",
    "GeneratedFile",
    "GenerateResult",
    "GenerationResult",
    "ImportResult",
    "ImportedContract",
    "InitResult",
    "LintResult",
    "ValidationIssue",
    "ValidationResult",
    "diff",
    "discover",
    "generate",
    "import_dbt",
    "init",
    "lint",
    "render",
    "to_yaml",
    "validate",
]
