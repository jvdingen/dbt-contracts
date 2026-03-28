"""Diff engine: compare generated output with on-disk state."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import pydantic as pyd

from dbt_contracts.core.discovery import DiscoveryResult
from dbt_contracts.core.generator import GeneratedFile, generate


class FileStatus(str, Enum):
    """Status of a file in the diff."""

    new = "new"
    modified = "modified"
    unchanged = "unchanged"


class FileDiff(pyd.BaseModel):
    """A single file comparison result."""

    path: Path
    status: FileStatus
    expected_content: str
    current_content: str | None = None


class DiffResult(pyd.BaseModel):
    """Result of comparing generated vs on-disk files."""

    diffs: list[FileDiff] = pyd.Field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return any(
            d.status in (FileStatus.new, FileStatus.modified) for d in self.diffs
        )

    @property
    def new_files(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == FileStatus.new]

    @property
    def modified_files(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == FileStatus.modified]

    @property
    def unchanged_files(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == FileStatus.unchanged]


def diff(
    discovery: DiscoveryResult,
    output_base: Path,
    models_dir: str | None = None,
    sources_dir: str | None = None,
) -> DiffResult:
    """Compare expected generated output with current on-disk state.

    Args:
        discovery: Result from discover().
        output_base: Base path for output (the dbt project root).
        models_dir: Override for models output directory.
        sources_dir: Override for sources output directory.

    Returns:
        DiffResult with per-file comparison.
    """
    gen_result = generate(
        discovery,
        output_base=output_base,
        models_dir=models_dir,
        sources_dir=sources_dir,
        dry_run=True,
    )

    diffs: list[FileDiff] = []

    for f in gen_result.files:
        diffs.append(_compare_file(f))

    return DiffResult(diffs=diffs)


def _compare_file(expected: GeneratedFile) -> FileDiff:
    """Compare a single expected file with its on-disk counterpart."""
    if not expected.path.exists():
        return FileDiff(
            path=expected.path,
            status=FileStatus.new,
            expected_content=expected.content,
        )

    current = expected.path.read_text(encoding="utf-8")
    if current == expected.content:
        return FileDiff(
            path=expected.path,
            status=FileStatus.unchanged,
            expected_content=expected.content,
            current_content=current,
        )

    return FileDiff(
        path=expected.path,
        status=FileStatus.modified,
        expected_content=expected.content,
        current_content=current,
    )
