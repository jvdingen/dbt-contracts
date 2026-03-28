"""Tests for contract and product validation."""

from pathlib import Path

from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.core.discovery import (
    DiscoveredContract,
    DiscoveredProduct,
    DiscoveryResult,
    discover,
)
from dbt_contracts.core.validation import ValidationResult, validate
from dbt_contracts.models.config import Config, ValidationConfig
from dbt_contracts.models.odps import OpenDataProductStandard

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


class TestValidateHappyPath:
    def test_valid_project_passes(self):
        discovery = discover(SAMPLE_PROJECT)
        result = validate(discovery)
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.issues == []


class TestValidateCrossReference:
    def test_unknown_input_contract(self):
        product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: bad-product
version: 1.0.0
status: active
name: Bad Product
inputPorts:
  - name: ghost-input
    contractId: nonexistent-contract
"""
        )
        discovery = DiscoveryResult(
            config=Config(),
            contracts=[],
            products=[DiscoveredProduct(path=Path("bad.odps.yaml"), product=product)],
        )
        result = validate(discovery)
        assert result.passed is False
        assert len(result.issues) == 1
        assert "nonexistent-contract" in result.issues[0].message
        assert "inputPort" in result.issues[0].message

    def test_unknown_output_contract(self):
        product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: bad-product
version: 1.0.0
status: active
name: Bad Product
outputPorts:
  - name: ghost-output
    contractId: nonexistent-contract
"""
        )
        discovery = DiscoveryResult(
            config=Config(),
            contracts=[],
            products=[DiscoveredProduct(path=Path("bad.odps.yaml"), product=product)],
        )
        result = validate(discovery)
        assert result.passed is False
        assert "outputPort" in result.issues[0].message

    def test_valid_cross_reference_passes(self):
        contract = OpenDataContractStandard.from_string(
            """
kind: DataContract
apiVersion: v3.1.0
id: my-contract
version: 1.0.0
status: active
"""
        )
        product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: my-product
version: 1.0.0
status: active
name: My Product
inputPorts:
  - name: my-input
    contractId: my-contract
"""
        )
        discovery = DiscoveryResult(
            config=Config(),
            contracts=[
                DiscoveredContract(path=Path("my.odcs.yaml"), contract=contract)
            ],
            products=[DiscoveredProduct(path=Path("my.odps.yaml"), product=product)],
        )
        result = validate(discovery)
        # Only cross-ref issues checked here; lint may still find issues
        xref_issues = [i for i in result.issues if "references unknown" in i.message]
        assert xref_issues == []


class TestValidateCrossReferenceDisabled:
    def test_skips_cross_ref_when_disabled(self):
        product = OpenDataProductStandard.from_string(
            """
kind: DataProduct
apiVersion: v1.0.0
id: loose-product
version: 1.0.0
status: active
name: Loose Product
inputPorts:
  - name: ghost
    contractId: nonexistent
"""
        )
        config = Config(validation=ValidationConfig(cross_reference=False))
        discovery = DiscoveryResult(
            config=config,
            contracts=[],
            products=[DiscoveredProduct(path=Path("loose.odps.yaml"), product=product)],
        )
        result = validate(discovery)
        xref_issues = [i for i in result.issues if "references unknown" in i.message]
        assert xref_issues == []


class TestValidateStatus:
    def _make_discovery(self, contract_status, min_status):
        contract = OpenDataContractStandard.from_string(
            f"""
kind: DataContract
apiVersion: v3.1.0
id: status-test
version: 1.0.0
status: {contract_status}
"""
        )
        config = Config(validation=ValidationConfig(min_status=min_status))
        return DiscoveryResult(
            config=config,
            contracts=[
                DiscoveredContract(path=Path("test.odcs.yaml"), contract=contract)
            ],
        )

    def test_status_meets_minimum(self):
        discovery = self._make_discovery("active", "draft")
        result = validate(discovery)
        status_issues = [i for i in result.issues if "below minimum" in i.message]
        assert status_issues == []

    def test_status_below_minimum(self):
        discovery = self._make_discovery("proposed", "active")
        result = validate(discovery)
        status_issues = [i for i in result.issues if "below minimum" in i.message]
        assert len(status_issues) == 1
        assert "'proposed'" in status_issues[0].message
        assert "'active'" in status_issues[0].message

    def test_equal_status_passes(self):
        discovery = self._make_discovery("draft", "draft")
        result = validate(discovery)
        status_issues = [i for i in result.issues if "below minimum" in i.message]
        assert status_issues == []


class TestValidateLint:
    def test_invalid_contract_reports_lint_error(self):
        contract = OpenDataContractStandard.from_string(
            """
kind: DataContract
apiVersion: v3.1.0
id: bad-contract
"""
        )
        discovery = DiscoveryResult(
            config=Config(),
            contracts=[
                DiscoveredContract(path=Path("bad.odcs.yaml"), contract=contract)
            ],
        )
        result = validate(discovery)
        assert result.passed is False
        assert any(i.contract_id == "bad-contract" for i in result.issues)
