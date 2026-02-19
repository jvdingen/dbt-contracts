"""Tests for ODCS quality rules to dbt tests conversion."""

from __future__ import annotations

import yaml
from open_data_contract_standard.model import DataQuality, OpenDataContractStandard

from dbt_contracts.generators.quality import inject_quality_tests, quality_rules_to_dbt_tests


class TestSqlRule:
    """SQL quality rules produce dbt_utils.expression_is_true tests."""

    def test_sql_quality_rule_to_dbt_test(self) -> None:
        """SQL rule with query produces expression_is_true test."""
        rules = [DataQuality(type="sql", query="amount > 0", description="Positive amounts")]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        assert "dbt_utils.expression_is_true" in tests[0]
        assert tests[0]["dbt_utils.expression_is_true"]["expression"] == "amount > 0"
        assert tests[0]["dbt_utils.expression_is_true"]["name"] == "Positive amounts"

    def test_sql_rule_without_query_skipped(self) -> None:
        """SQL rule without query is skipped."""
        rules = [DataQuality(type="sql")]
        tests = quality_rules_to_dbt_tests(rules)
        assert tests == []


class TestCustomDbtRule:
    """Custom dbt engine rules pass through implementation."""

    def test_custom_dbt_engine_dict(self) -> None:
        """Custom rule with dict implementation is passed through."""
        impl = {"my_custom_test": {"arg1": "value1"}}
        rules = [DataQuality(type="custom", engine="dbt", implementation=impl)]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        assert "my_custom_test" in tests[0]
        assert tests[0]["my_custom_test"]["arg1"] == "value1"

    def test_custom_dbt_engine_string(self) -> None:
        """Custom rule with string implementation is passed through as raw string."""
        rules = [DataQuality(type="custom", engine="dbt", implementation="my_simple_test")]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        assert tests[0] == "my_simple_test"

    def test_custom_without_implementation_skipped(self) -> None:
        """Custom rule without implementation is skipped."""
        rules = [DataQuality(type="custom", engine="dbt")]
        tests = quality_rules_to_dbt_tests(rules)
        assert tests == []

    def test_custom_non_dbt_engine_skipped(self) -> None:
        """Custom rule with non-dbt engine is skipped."""
        rules = [DataQuality(type="custom", engine="spark", implementation="some_test")]
        tests = quality_rules_to_dbt_tests(rules)
        assert tests == []


class TestLibraryMetrics:
    """Library metric rules map to dbt_expectations tests."""

    def test_library_row_count(self) -> None:
        """RowCount metric maps to expect_table_row_count_to_be_between."""
        rules = [DataQuality(metric="rowCount", mustBeGreaterOrEqualTo=1, mustBeLessOrEqualTo=1000)]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        key = "dbt_expectations.expect_table_row_count_to_be_between"
        assert key in tests[0]
        assert tests[0][key]["min_value"] == 1
        assert tests[0][key]["max_value"] == 1000

    def test_library_row_count_with_between(self) -> None:
        """RowCount with mustBeBetween uses both bounds."""
        rules = [DataQuality(metric="rowCount", mustBeBetween=[10, 500])]
        tests = quality_rules_to_dbt_tests(rules)

        key = "dbt_expectations.expect_table_row_count_to_be_between"
        assert tests[0][key]["min_value"] == 10
        assert tests[0][key]["max_value"] == 500

    def test_library_null_values(self) -> None:
        """NullValues metric maps to expect_column_values_to_not_be_null."""
        rules = [DataQuality(metric="nullValues", mustBe=0)]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        key = "dbt_expectations.expect_column_values_to_not_be_null"
        assert key in tests[0]

    def test_library_duplicate_values(self) -> None:
        """DuplicateValues metric maps to expect_column_values_to_be_unique."""
        rules = [DataQuality(metric="duplicateValues", mustBe=0)]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        key = "dbt_expectations.expect_column_values_to_be_unique"
        assert key in tests[0]


class TestSeverity:
    """Severity field adds config.severity to test entries."""

    def test_severity_propagated(self) -> None:
        """Severity on a rule adds config.severity to the test entry."""
        rules = [DataQuality(type="sql", query="1=1", severity="warn")]
        tests = quality_rules_to_dbt_tests(rules)

        assert len(tests) == 1
        assert tests[0]["config"]["severity"] == "warn"

    def test_severity_on_library_metric(self) -> None:
        """Severity works with library metric rules too."""
        rules = [DataQuality(metric="duplicateValues", mustBe=0, severity="error")]
        tests = quality_rules_to_dbt_tests(rules)

        key = "dbt_expectations.expect_column_values_to_be_unique"
        assert tests[0][key] == {}
        assert tests[0]["config"]["severity"] == "error"


class TestUnknownRuleType:
    """Unsupported rule types are silently skipped."""

    def test_unknown_rule_type_ignored(self) -> None:
        """Unknown rule type produces no tests."""
        rules = [DataQuality(type="greatExpectations", description="Unknown rule")]
        tests = quality_rules_to_dbt_tests(rules)
        assert tests == []

    def test_unknown_metric_ignored(self) -> None:
        """Unknown metric produces no tests."""
        rules = [DataQuality(metric="unknownMetric")]
        tests = quality_rules_to_dbt_tests(rules)
        assert tests == []


class TestInjectQualityTests:
    """inject_quality_tests merges quality tests into exported YAML."""

    def _make_contract(self) -> OpenDataContractStandard:
        """Build a minimal contract with quality rules for testing."""
        return OpenDataContractStandard.model_validate(
            {
                "kind": "DataContract",
                "apiVersion": "v3.1.0",
                "id": "test-id",
                "name": "Test Contract",
                "version": "1.0.0",
                "status": "active",
                "schema": [
                    {
                        "name": "my_model",
                        "physicalType": "table",
                        "quality": [
                            {"type": "sql", "query": "amount > 0"},
                        ],
                        "properties": [
                            {
                                "name": "col_a",
                                "logicalType": "string",
                                "quality": [
                                    {"metric": "duplicateValues", "mustBe": 0},
                                ],
                            },
                        ],
                    },
                ],
            },
        )

    def test_inject_quality_tests_roundtrip(self) -> None:
        """Injecting tests preserves existing content and adds quality tests."""
        input_yaml = yaml.safe_dump(
            {
                "version": 2,
                "models": [
                    {
                        "name": "my_model",
                        "columns": [
                            {"name": "col_a", "data_tests": ["not_null"]},
                        ],
                    },
                ],
            },
            sort_keys=False,
        )

        contract = self._make_contract()
        result = inject_quality_tests(input_yaml, contract)
        data = yaml.safe_load(result)

        model = data["models"][0]
        # Table-level test injected
        assert "data_tests" in model
        assert any("dbt_utils.expression_is_true" in t for t in model["data_tests"] if isinstance(t, dict))

        # Column-level test injected, existing preserved
        col_a = model["columns"][0]
        assert "not_null" in col_a["data_tests"]
        assert any(
            "dbt_expectations.expect_column_values_to_be_unique" in t
            for t in col_a["data_tests"]
            if isinstance(t, dict)
        )

    def test_inject_no_schema_returns_unchanged(self) -> None:
        """Contract with no schema returns YAML unchanged."""
        contract = OpenDataContractStandard.model_validate(
            {
                "kind": "DataContract",
                "apiVersion": "v3.1.0",
                "id": "test",
                "name": "Empty",
                "version": "1.0.0",
                "status": "active",
            },
        )
        input_yaml = "version: 2\nmodels: []\n"
        assert inject_quality_tests(input_yaml, contract) == input_yaml
