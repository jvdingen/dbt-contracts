"""Validation of discovered contracts and products.

Runs ODCS schema validation via the adapter, validates ODPS products,
and checks cross-references between products and contracts.
"""

from __future__ import annotations

import pydantic as pyd

from dbt_contracts.core.adapter import lint
from dbt_contracts.core.discovery import DiscoveryResult

STATUS_ORDER = ["proposed", "draft", "active", "deprecated", "retired"]


class ValidationIssue(pyd.BaseModel):
    """A single validation problem."""

    path: str
    contract_id: str | None = None
    message: str


class ValidationResult(pyd.BaseModel):
    """Result of validating all discovered contracts and products."""

    issues: list[ValidationIssue] = pyd.Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0


def validate(discovery: DiscoveryResult) -> ValidationResult:
    """Validate all discovered contracts and products.

    Runs:
    1. ODCS schema validation (via datacontract-cli lint)
    2. Cross-reference validation (ODPS contractId -> ODCS)
    3. Status threshold checks (against config.validation.min_status)

    Args:
        discovery: Result from discover().

    Returns:
        ValidationResult with any issues found.
    """
    issues: list[ValidationIssue] = []

    contract_ids = {dc.contract.id for dc in discovery.contracts if dc.contract.id}

    validation_config = discovery.config.validation
    min_status = validation_config.min_status if validation_config else "draft"
    cross_reference = validation_config.cross_reference if validation_config else True

    # 1. Validate each ODCS contract
    for dc in discovery.contracts:
        lint_result = lint(dc.contract)
        if not lint_result.passed:
            for error in lint_result.errors:
                issues.append(
                    ValidationIssue(
                        path=str(dc.path),
                        contract_id=dc.contract.id,
                        message=error,
                    )
                )

        if min_status and dc.contract.status:
            issue = _check_status(
                str(dc.path), dc.contract.id, dc.contract.status, min_status
            )
            if issue:
                issues.append(issue)

    # 2. Cross-reference: ODPS contractId -> ODCS contracts
    if cross_reference:
        for dp in discovery.products:
            for port_type in ("inputPorts", "outputPorts"):
                for port in getattr(dp.product, port_type, None) or []:
                    if port.contractId and port.contractId not in contract_ids:
                        label = port_type.rstrip("s")
                        issues.append(
                            ValidationIssue(
                                path=str(dp.path),
                                contract_id=dp.product.id,
                                message=(
                                    f"{label} references unknown contract:"
                                    f" {port.contractId}"
                                ),
                            )
                        )

    return ValidationResult(issues=issues)


def _check_status(
    path: str,
    contract_id: str | None,
    status: str,
    min_status: str,
) -> ValidationIssue | None:
    """Check if a contract's status meets the minimum threshold."""
    if status not in STATUS_ORDER or min_status not in STATUS_ORDER:
        return None
    if STATUS_ORDER.index(status) < STATUS_ORDER.index(min_status):
        return ValidationIssue(
            path=path,
            contract_id=contract_id,
            message=f"Status '{status}' is below minimum '{min_status}'",
        )
    return None
