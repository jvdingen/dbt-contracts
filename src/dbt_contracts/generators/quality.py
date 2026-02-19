"""Convert ODCS quality rules to dbt test entries and inject them into schema YAML."""

from __future__ import annotations

import logging
from typing import Any

import yaml
from open_data_contract_standard.model import DataQuality, OpenDataContractStandard

logger = logging.getLogger(__name__)


def _wrap_with_severity(test_entry: dict[str, Any], rule: DataQuality) -> dict[str, Any]:
    """Add ``config.severity`` to a test entry if the rule specifies severity."""
    if rule.severity:
        test_entry.setdefault("config", {})["severity"] = rule.severity
    return test_entry


def _sql_rule_to_test(rule: DataQuality) -> dict[str, Any] | None:
    """Convert a ``type: sql`` quality rule to a ``dbt_utils.expression_is_true`` test."""
    if not rule.query:
        logger.warning("Skipping SQL quality rule without query: %s", rule.description or rule.id)
        return None
    entry: dict[str, Any] = {"dbt_utils.expression_is_true": {"expression": rule.query}}
    if rule.description:
        entry["dbt_utils.expression_is_true"]["name"] = rule.description
    return _wrap_with_severity(entry, rule)


def _custom_dbt_rule_to_test(rule: DataQuality) -> dict[str, Any] | str | None:
    """Convert a ``type: custom, engine: dbt`` quality rule to a test entry."""
    if rule.implementation is None:
        logger.warning("Skipping custom dbt rule without implementation: %s", rule.description or rule.id)
        return None
    if isinstance(rule.implementation, dict):
        entry = dict(rule.implementation)
        return _wrap_with_severity(entry, rule)
    # String implementation — return as raw test name
    return rule.implementation


def _row_count_to_test(rule: DataQuality) -> dict[str, Any]:
    """Convert a ``metric: rowCount`` rule to ``dbt_expectations.expect_table_row_count_to_be_between``."""
    params: dict[str, Any] = {}
    if rule.mustBeGreaterThan is not None:
        params["min_value"] = rule.mustBeGreaterThan + 1
    if rule.mustBeGreaterOrEqualTo is not None:
        params["min_value"] = rule.mustBeGreaterOrEqualTo
    if rule.mustBeLessThan is not None:
        params["max_value"] = rule.mustBeLessThan - 1
    if rule.mustBeLessOrEqualTo is not None:
        params["max_value"] = rule.mustBeLessOrEqualTo
    if rule.mustBeBetween is not None:
        params["min_value"] = rule.mustBeBetween[0]
        params["max_value"] = rule.mustBeBetween[1]
    entry: dict[str, Any] = {"dbt_expectations.expect_table_row_count_to_be_between": params}
    return _wrap_with_severity(entry, rule)


def _null_values_to_test(rule: DataQuality) -> dict[str, Any]:
    """Convert a ``metric: nullValues`` rule to ``dbt_expectations.expect_column_values_to_not_be_null``."""
    params: dict[str, Any] = {}
    if rule.mustBeLessOrEqualTo is not None and rule.mustBeLessOrEqualTo > 0:
        params["mostly"] = 1.0 - rule.mustBeLessOrEqualTo
    entry: dict[str, Any] = {"dbt_expectations.expect_column_values_to_not_be_null": params}
    return _wrap_with_severity(entry, rule)


def _duplicate_values_to_test(rule: DataQuality) -> dict[str, Any]:
    """Convert a ``metric: duplicateValues`` rule to ``dbt_expectations.expect_column_values_to_be_unique``."""
    entry: dict[str, Any] = {"dbt_expectations.expect_column_values_to_be_unique": {}}
    return _wrap_with_severity(entry, rule)


_LIBRARY_METRIC_CONVERTERS = {
    "rowCount": _row_count_to_test,
    "nullValues": _null_values_to_test,
    "duplicateValues": _duplicate_values_to_test,
}


def quality_rules_to_dbt_tests(quality: list[DataQuality]) -> list[dict[str, Any] | str]:
    """Convert a list of ODCS quality rules to dbt test entries.

    Returns a list of dicts or strings suitable for inclusion in a ``data_tests`` array.
    Unsupported rule types are silently skipped.
    """
    tests: list[dict[str, Any] | str] = []
    for rule in quality:
        entry: dict[str, Any] | str | None = None

        if rule.type == "sql":
            entry = _sql_rule_to_test(rule)
        elif rule.type == "custom" and rule.engine == "dbt":
            entry = _custom_dbt_rule_to_test(rule)
        elif rule.metric and rule.metric in _LIBRARY_METRIC_CONVERTERS:
            entry = _LIBRARY_METRIC_CONVERTERS[rule.metric](rule)
        else:
            logger.debug("Skipping unsupported quality rule type=%s metric=%s", rule.type, rule.metric)
            continue

        if entry is not None:
            tests.append(entry)

    return tests


def inject_quality_tests(model_yaml: str, contract: OpenDataContractStandard) -> str:
    """Inject quality-derived dbt tests into an exported model YAML string.

    Reads quality rules from the contract's schema objects (table-level) and
    properties (column-level), converts them, and merges them into the
    ``data_tests`` lists in the YAML.
    """
    if not contract.schema_:
        return model_yaml

    data = yaml.safe_load(model_yaml)
    if not data or "models" not in data:
        return model_yaml

    for model in data["models"]:
        model_name = model.get("name")
        # Find the matching schema object
        schema_obj = next(
            (s for s in contract.schema_ if getattr(s, "name", None) == model_name),
            None,
        )
        if schema_obj is None:
            continue

        # Inject table-level quality tests
        table_quality = getattr(schema_obj, "quality", None) or []
        if table_quality:
            table_tests = quality_rules_to_dbt_tests(table_quality)
            if table_tests:
                existing = model.get("data_tests", [])
                model["data_tests"] = existing + table_tests

        # Inject column-level quality tests
        properties = getattr(schema_obj, "properties", None) or []
        columns = model.get("columns", [])
        for prop in properties:
            prop_name = getattr(prop, "name", None)
            prop_quality = getattr(prop, "quality", None) or []
            if not prop_name or not prop_quality:
                continue

            col = next((c for c in columns if c.get("name") == prop_name), None)
            if col is None:
                continue

            col_tests = quality_rules_to_dbt_tests(prop_quality)
            if col_tests:
                existing = col.get("data_tests", [])
                col["data_tests"] = existing + col_tests

    return yaml.safe_dump(data, sort_keys=False)
