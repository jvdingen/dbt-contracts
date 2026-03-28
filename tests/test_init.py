"""Tests for the init module."""

from dbt_contracts.core.init import InitResult, init


class TestInit:
    def test_returns_init_result(self, tmp_path):
        result = init(tmp_path)
        assert isinstance(result, InitResult)

    def test_creates_directory_structure(self, tmp_path):
        init(tmp_path)
        assert (tmp_path / "contracts").is_dir()
        assert (tmp_path / "contracts" / "contracts").is_dir()
        assert (tmp_path / "contracts" / "products").is_dir()

    def test_creates_config_yaml(self, tmp_path):
        result = init(tmp_path)
        assert result.config_path is not None
        assert result.config_path.exists()
        content = result.config_path.read_text(encoding="utf-8")
        assert "dbt_project_dir" in content
        assert "dbt-contracts configuration" in content

    def test_created_flag_true(self, tmp_path):
        result = init(tmp_path)
        assert result.created is True

    def test_skips_existing_directory(self, tmp_path):
        (tmp_path / "contracts").mkdir()
        result = init(tmp_path)
        assert result.created is False
        assert result.config_path is None

    def test_force_overwrites_existing(self, tmp_path):
        (tmp_path / "contracts").mkdir()
        result = init(tmp_path, force=True)
        assert result.created is True
        assert (tmp_path / "contracts" / "config.yaml").exists()

    def test_detects_dbt_project_yml(self, tmp_path):
        (tmp_path / "dbt_project.yml").write_text("name: my_project\n")
        result = init(tmp_path)
        content = result.config_path.read_text(encoding="utf-8")
        assert 'dbt_project_dir: ".."' in content
