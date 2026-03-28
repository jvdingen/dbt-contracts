"""Tests for the init CLI command."""

from dbt_contracts.cli import cli


class TestInitCommand:
    def test_init_creates_directory(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Initialized" in result.output
        assert (tmp_path / "contracts").is_dir()

    def test_init_existing_exits_one(self, runner, tmp_path):
        (tmp_path / "contracts").mkdir()
        result = runner.invoke(cli, ["init", "--dir", str(tmp_path)])
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_force_overwrites(self, runner, tmp_path):
        (tmp_path / "contracts").mkdir()
        result = runner.invoke(cli, ["init", "--dir", str(tmp_path), "--force"])
        assert result.exit_code == 0
        assert "Initialized" in result.output

    def test_init_shows_next_steps(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--dir", str(tmp_path)])
        assert "Next steps" in result.output

    def test_init_shows_in_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "init" in result.output
