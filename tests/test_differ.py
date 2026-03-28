"""Tests for the diff module."""

from pathlib import Path

from dbt_contracts.core.differ import DiffResult, FileStatus, diff
from dbt_contracts.core.discovery import discover
from dbt_contracts.core.generator import generate

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PROJECT = FIXTURES / "sample_project"


class TestDiff:
    def test_returns_diff_result(self, tmp_path):
        discovery = discover(SAMPLE_PROJECT)
        result = diff(discovery, output_base=tmp_path)
        assert isinstance(result, DiffResult)

    def test_all_new_when_no_files_exist(self, tmp_path):
        discovery = discover(SAMPLE_PROJECT)
        result = diff(discovery, output_base=tmp_path)
        assert result.has_drift
        assert len(result.new_files) > 0
        assert len(result.modified_files) == 0

    def test_all_unchanged_after_generate(self, tmp_path):
        discovery = discover(SAMPLE_PROJECT)
        generate(discovery, output_base=tmp_path)
        result = diff(discovery, output_base=tmp_path)
        assert not result.has_drift
        assert all(d.status == FileStatus.unchanged for d in result.diffs)

    def test_detects_modified_file(self, tmp_path):
        discovery = discover(SAMPLE_PROJECT)
        generate(discovery, output_base=tmp_path)
        # Modify a generated file
        yml_files = list(tmp_path.rglob("*.yml"))
        assert len(yml_files) > 0
        yml_files[0].write_text("# modified\nversion: 2\n")
        result = diff(discovery, output_base=tmp_path)
        assert result.has_drift
        assert len(result.modified_files) > 0

    def test_has_drift_false_when_unchanged(self, tmp_path):
        discovery = discover(SAMPLE_PROJECT)
        generate(discovery, output_base=tmp_path)
        result = diff(discovery, output_base=tmp_path)
        assert not result.has_drift
