"""Pure post-processing functions for dbt artifacts (string in → string out)."""

from __future__ import annotations

import re

import yaml


def rename_source(source_yaml: str, old_name: str, new_name: str) -> str:
    """Replace a source name in a dbt sources.yml YAML string.

    Parses the YAML, finds the source entry matching *old_name*, renames it
    to *new_name*, and returns the re-serialised YAML.
    """
    data = yaml.safe_load(source_yaml)
    for source in data.get("sources", []):
        if source.get("name") == old_name:
            source["name"] = new_name
    return yaml.safe_dump(data, sort_keys=False)


def _merge_yaml_lists(yamls: list[str], key: str) -> str:
    """Merge multiple dbt YAML strings by concatenating a top-level list key."""
    items: list[dict] = []
    for y in yamls:
        data = yaml.safe_load(y)
        items.extend(data.get(key, []))
    return yaml.safe_dump({"version": 2, key: items}, sort_keys=False)


def merge_sources(yamls: list[str]) -> str:
    """Merge multiple dbt sources.yml YAML strings into one document."""
    return _merge_yaml_lists(yamls, "sources")


def merge_models(yamls: list[str]) -> str:
    """Merge multiple dbt schema.yml YAML strings into one document."""
    return _merge_yaml_lists(yamls, "models")


def rewrite_source_refs(sql: str, old_name: str, new_name: str) -> str:
    """Replace the source name inside ``{{ source('...', ...) }}`` calls in SQL.

    Handles both single- and double-quoted source names.
    """
    pattern = r"\{\{\s*source\(\s*['\"]" + re.escape(old_name) + r"['\"]"
    replacement = "{{ source('" + new_name + "'"
    return re.sub(pattern, replacement, sql)
