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


def merge_sources(yamls: list[str]) -> str:
    """Merge multiple dbt sources.yml YAML strings into one document."""
    sources: list[dict] = []
    for y in yamls:
        data = yaml.safe_load(y)
        sources.extend(data.get("sources", []))
    return yaml.safe_dump({"version": 2, "sources": sources}, sort_keys=False)


def merge_models(yamls: list[str]) -> str:
    """Merge multiple dbt schema.yml YAML strings into one document."""
    models: list[dict] = []
    for y in yamls:
        data = yaml.safe_load(y)
        models.extend(data.get("models", []))
    return yaml.safe_dump({"version": 2, "models": models}, sort_keys=False)


def rewrite_source_refs(sql: str, old_name: str, new_name: str) -> str:
    """Replace the source name inside ``{{ source('...', ...) }}`` calls in SQL.

    Handles both single- and double-quoted source names.
    """
    pattern = r"\{\{\s*source\(\s*['\"]" + re.escape(old_name) + r"['\"]"
    replacement = "{{ source('" + new_name + "'"
    return re.sub(pattern, replacement, sql)
