"""Tests for drift detection and prompt behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from dbt_contracts.cli import cli
from dbt_contracts.generators.orchestrator import DriftStatus, plan_for_product

ODPS_FIXTURES = Path(__file__).parent / "fixtures" / "odps"
ODCS_FIXTURES = Path(__file__).parent / "fixtures" / "odcs"


class TestDriftStatus:
    """plan_for_product returns correct drift status."""

    def test_new_files(self, tmp_path: Path) -> None:
        """Files that don't exist on disk are marked NEW."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"
        files = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
        )
        assert len(files) > 0
        assert all(f.drift_status == DriftStatus.NEW for f in files)

    def test_unchanged_files(self, tmp_path: Path) -> None:
        """Files matching disk content are marked UNCHANGED."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"

        # First pass: plan and write
        files = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
        )
        for f in files:
            f.path.parent.mkdir(parents=True, exist_ok=True)
            f.path.write_text(f.content)

        # Second pass: plan again — should all be UNCHANGED
        files2 = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
        )
        assert len(files2) > 0
        assert all(f.drift_status == DriftStatus.UNCHANGED for f in files2)

    def test_changed_files(self, tmp_path: Path) -> None:
        """Files differing from disk content are marked CHANGED."""
        models_dir = tmp_path / "models"
        sources_dir = tmp_path / "sources"

        # First pass: plan and write
        files = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
        )
        for f in files:
            f.path.parent.mkdir(parents=True, exist_ok=True)
            f.path.write_text("old content that differs")

        # Second pass: plan again — should all be CHANGED
        files2 = plan_for_product(
            ODPS_FIXTURES / "generation_product.odps.yaml",
            ODCS_FIXTURES,
            models_dir,
            sources_dir,
        )
        assert len(files2) > 0
        assert all(f.drift_status == DriftStatus.CHANGED for f in files2)


class TestRunGenerateDrift:
    """run_generate handles drift correctly."""

    def test_new_files_written_without_prompt(self, tmp_path: Path) -> None:
        """New files are written directly without prompting."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            root = Path(td)
            _setup_generation_fixtures(root)

            result = runner.invoke(cli, ["generate"])
            assert result.exit_code == 0
            assert "Created" in result.output

    def test_unchanged_files_skipped(self, tmp_path: Path) -> None:
        """Unchanged files are reported as unchanged."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            root = Path(td)
            _setup_generation_fixtures(root)

            # First generate
            runner.invoke(cli, ["generate"])
            # Second generate — everything should be unchanged
            result = runner.invoke(cli, ["generate"])
            assert result.exit_code == 0
            assert "Unchanged" in result.output
            assert "Created" not in result.output

    def test_yolo_mode_writes_changed_without_prompt(self, tmp_path: Path) -> None:
        """--yolo-mode writes changed files without prompting."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            root = Path(td)
            _setup_generation_fixtures(root)

            # First generate
            runner.invoke(cli, ["generate"])
            # Modify a generated file to create drift
            _mutate_generated_files(root)

            result = runner.invoke(cli, ["generate", "--yolo-mode"])
            assert result.exit_code == 0
            assert "Updated" in result.output

    def test_dry_run_shows_drift_no_writes(self, tmp_path: Path) -> None:
        """--dry-run shows drift but does not write files."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            root = Path(td)
            _setup_generation_fixtures(root)

            # First generate
            runner.invoke(cli, ["generate"])
            # Modify a generated file to create drift
            _mutate_generated_files(root)

            # Capture mutated content
            sources_path = root / "sources" / "sources.yml"
            mutated_content = sources_path.read_text()

            result = runner.invoke(cli, ["generate", "--dry-run"])
            assert result.exit_code == 0
            assert "Drift detected" in result.output
            # File should NOT have been overwritten
            assert sources_path.read_text() == mutated_content

    def test_interactive_prompts_for_changed(self, tmp_path: Path) -> None:
        """Interactive mode prompts even when yolo_mode would be set."""
        from dbt_contracts.commands.generate import run_generate
        from dbt_contracts.config import Config
        from rich.console import Console

        root = tmp_path
        _setup_generation_fixtures(root)

        config = Config()
        console = Console(file=open(tmp_path / "output.txt", "w"))

        # First generate to create files
        run_generate(config, root, console)
        # Modify to create drift
        _mutate_generated_files(root)

        # Mock questionary to say "No" to all
        with patch("dbt_contracts.commands.generate.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "No"
            run_generate(config, root, console, interactive=True, yolo_mode=True)
            # Should have prompted despite yolo_mode
            mock_q.select.assert_called()


def _setup_generation_fixtures(root: Path) -> None:
    """Set up a project directory with ODPS/ODCS fixtures for generation."""
    odps_dir = root / "contracts" / "products"
    odcs_dir = root / "contracts" / "schemas"
    odps_dir.mkdir(parents=True, exist_ok=True)
    odcs_dir.mkdir(parents=True, exist_ok=True)

    # Copy fixture files
    import shutil

    for f in ODPS_FIXTURES.iterdir():
        if f.name == "generation_product.odps.yaml":
            shutil.copy(f, odps_dir / f.name)
    for f in ODCS_FIXTURES.iterdir():
        shutil.copy(f, odcs_dir / f.name)


def _mutate_generated_files(root: Path) -> None:
    """Modify generated files to create drift."""
    sources_path = root / "sources" / "sources.yml"
    if sources_path.exists():
        sources_path.write_text("# mutated\n" + sources_path.read_text())
