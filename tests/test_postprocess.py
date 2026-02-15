"""Tests for dbt artifact post-processing functions (pure, no file I/O)."""

from __future__ import annotations

import yaml

from dbt_contracts.generators.postprocess import merge_models, merge_sources, rename_source

SAMPLE_SOURCE = """\
version: 2
sources:
- name: dbb7b1eb-7628-436e-8914-2a00638ba6db
  tables:
  - name: payments
    columns:
    - name: payment_id
"""

SAMPLE_MODEL = """\
version: 2
models:
- name: payments
  columns:
  - name: payment_id
"""


class TestRenameSource:
    """rename_source replaces source name in YAML."""

    def test_renames_matching_source(self) -> None:
        """Source matching old_name gets renamed to new_name."""
        result = rename_source(SAMPLE_SOURCE, "dbb7b1eb-7628-436e-8914-2a00638ba6db", "payments_input")
        data = yaml.safe_load(result)
        assert data["sources"][0]["name"] == "payments_input"

    def test_leaves_non_matching_source(self) -> None:
        """Source not matching old_name is left unchanged."""
        result = rename_source(SAMPLE_SOURCE, "no-match", "new_name")
        data = yaml.safe_load(result)
        assert data["sources"][0]["name"] == "dbb7b1eb-7628-436e-8914-2a00638ba6db"


class TestMergeSources:
    """merge_sources combines multiple sources YAML docs."""

    def test_merges_two_sources(self) -> None:
        """Two source documents merge into one with both sources."""
        source_a = "version: 2\nsources:\n- name: a\n  tables: []\n"
        source_b = "version: 2\nsources:\n- name: b\n  tables: []\n"
        result = merge_sources([source_a, source_b])
        data = yaml.safe_load(result)

        assert data["version"] == 2
        assert len(data["sources"]) == 2
        names = [s["name"] for s in data["sources"]]
        assert names == ["a", "b"]

    def test_single_source(self) -> None:
        """Single source document passes through."""
        result = merge_sources([SAMPLE_SOURCE])
        data = yaml.safe_load(result)
        assert len(data["sources"]) == 1


class TestMergeModels:
    """merge_models combines multiple models YAML docs."""

    def test_merges_two_models(self) -> None:
        """Two model documents merge into one with both models."""
        model_a = "version: 2\nmodels:\n- name: a\n"
        model_b = "version: 2\nmodels:\n- name: b\n"
        result = merge_models([model_a, model_b])
        data = yaml.safe_load(result)

        assert data["version"] == 2
        assert len(data["models"]) == 2
        names = [m["name"] for m in data["models"]]
        assert names == ["a", "b"]

    def test_single_model(self) -> None:
        """Single model document passes through."""
        result = merge_models([SAMPLE_MODEL])
        data = yaml.safe_load(result)
        assert len(data["models"]) == 1


