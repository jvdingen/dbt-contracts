"""Tests for dbt artifact post-processing functions (pure, no file I/O)."""

from __future__ import annotations

import yaml

from dbt_contracts.generators.postprocess import merge_models, merge_sources, rename_source, rewrite_source_refs

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


class TestRewriteSourceRefs:
    """rewrite_source_refs replaces source names in SQL."""

    def test_single_quote_replacement(self) -> None:
        """Single-quoted source name is replaced."""
        sql = "select * from {{ source('old-uuid', 'table') }}"
        result = rewrite_source_refs(sql, "old-uuid", "payments")
        assert "source('payments'" in result

    def test_double_quote_replacement(self) -> None:
        """Double-quoted source name is replaced."""
        sql = 'select * from {{ source("old-uuid", "table") }}'
        result = rewrite_source_refs(sql, "old-uuid", "payments")
        assert "source('payments'" in result

    def test_no_match_unchanged(self) -> None:
        """SQL without matching source name is unchanged."""
        sql = "select * from {{ source('other', 'table') }}"
        result = rewrite_source_refs(sql, "old-uuid", "payments")
        assert result == sql

    def test_uuid_source_ref(self) -> None:
        """Real UUID source ref gets rewritten."""
        sql = "    from {{ source('dbb7b1eb-7628-436e-8914-2a00638ba6db', 'payments') }}"
        result = rewrite_source_refs(sql, "dbb7b1eb-7628-436e-8914-2a00638ba6db", "my_input")
        assert "source('my_input'" in result
        assert "dbb7b1eb" not in result
