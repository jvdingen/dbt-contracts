"""Tests for ODCS/ODPS metadata propagation to dbt schema YAML."""

from __future__ import annotations

import yaml
from open_data_contract_standard.model import OpenDataContractStandard

from dbt_contracts.generators.metadata import _build_description, _resolve_owner, inject_metadata


def _make_contract(**overrides: object) -> OpenDataContractStandard:
    """Build a minimal contract, merging *overrides* into the base dict."""
    base: dict = {
        "kind": "DataContract",
        "apiVersion": "v3.1.0",
        "id": "test-meta",
        "name": "Meta Contract",
        "version": "1.0.0",
        "status": "active",
        "schema": [
            {
                "name": "my_model",
                "physicalType": "table",
                "properties": [
                    {"name": "col_a", "logicalType": "string"},
                ],
            },
        ],
    }
    base.update(overrides)
    return OpenDataContractStandard.model_validate(base)


def _base_yaml(**model_overrides: object) -> str:
    """Return a minimal dbt schema YAML string for injection tests."""
    model: dict = {"name": "my_model", "columns": [{"name": "col_a"}]}
    model.update(model_overrides)
    return yaml.safe_dump({"version": 2, "models": [model]}, sort_keys=False)


# ---------------------------------------------------------------------------
# _build_description
# ---------------------------------------------------------------------------


class TestBuildDescription:
    """Tests for the _build_description helper."""

    def test_full(self) -> None:
        """All three description fields produce formatted output."""
        contract = _make_contract(
            description={"purpose": "Purpose text.", "limitations": "Limits.", "usage": "Use wisely."},
        )
        result = _build_description(contract, None)
        assert result is not None
        assert "Purpose text." in result
        assert "**Limitations:** Limits." in result
        assert "**Usage:** Use wisely." in result

    def test_partial(self) -> None:
        """Only purpose set, others None."""
        contract = _make_contract(description={"purpose": "Just purpose."})
        result = _build_description(contract, None)
        assert result == "Just purpose."

    def test_falls_back_to_schema(self) -> None:
        """No contract description uses schema_obj.description."""
        contract = _make_contract()
        result = _build_description(contract, "Schema fallback")
        assert result == "Schema fallback"

    def test_empty_description_falls_back(self) -> None:
        """Description object with all None fields falls back to schema."""
        contract = _make_contract(description={})
        result = _build_description(contract, "Fallback")
        assert result == "Fallback"


# ---------------------------------------------------------------------------
# _resolve_owner
# ---------------------------------------------------------------------------


class TestResolveOwner:
    """Tests for the _resolve_owner helper."""

    def test_from_team_object(self) -> None:
        """Team with members, finds role='owner'."""
        contract = _make_contract(
            team={
                "name": "Platform Team",
                "members": [
                    {"name": "Dev Person", "role": "developer"},
                    {"name": "Owner Person", "role": "owner"},
                ],
            },
        )
        assert _resolve_owner(contract.team) == "Owner Person"

    def test_from_team_name(self) -> None:
        """Team without members, uses team.name."""
        contract = _make_contract(team={"name": "Fallback Team"})
        assert _resolve_owner(contract.team) == "Fallback Team"

    def test_from_member_list(self) -> None:
        """Bare list[TeamMember], finds role='owner'."""
        contract = _make_contract(
            team=[
                {"name": "Dev", "role": "developer"},
                {"name": "List Owner", "role": "owner"},
            ],
        )
        assert _resolve_owner(contract.team) == "List Owner"

    def test_none(self) -> None:
        """No team returns None."""
        contract = _make_contract()
        assert _resolve_owner(contract.team) is None


# ---------------------------------------------------------------------------
# inject_metadata
# ---------------------------------------------------------------------------


class TestInjectTags:
    """Tags from contract and product are merged onto the model."""

    def test_merged(self) -> None:
        """Contract + product tags both appear on model."""
        contract = _make_contract(tags=["finance", "pii"])
        result = inject_metadata(_base_yaml(), contract, product_tags=["production", "daily"])
        data = yaml.safe_load(result)
        tags = data["models"][0]["tags"]
        assert "finance" in tags
        assert "pii" in tags
        assert "production" in tags
        assert "daily" in tags

    def test_deduplication(self) -> None:
        """Duplicate tags across contract and product are merged once."""
        contract = _make_contract(tags=["shared", "finance"])
        result = inject_metadata(_base_yaml(), contract, product_tags=["shared", "daily"])
        data = yaml.safe_load(result)
        tags = data["models"][0]["tags"]
        assert tags.count("shared") == 1

    def test_preserves_existing_tags(self) -> None:
        """Existing model tags are preserved when merging."""
        contract = _make_contract(tags=["new_tag"])
        input_yaml = _base_yaml(tags=["existing_tag"])
        result = inject_metadata(input_yaml, contract)
        data = yaml.safe_load(result)
        tags = data["models"][0]["tags"]
        assert "existing_tag" in tags
        assert "new_tag" in tags


class TestInjectDomain:
    """Product domain appears in model.config.meta.domain."""

    def test_inject_domain(self) -> None:
        """Product domain is set in meta."""
        contract = _make_contract()
        result = inject_metadata(_base_yaml(), contract, product_domain="analytics")
        data = yaml.safe_load(result)
        assert data["models"][0]["config"]["meta"]["domain"] == "analytics"


class TestInjectOwner:
    """Owner from contract team appears in model.config.meta.owner."""

    def test_inject_owner(self) -> None:
        """Owner is extracted and placed in meta."""
        contract = _make_contract(
            team={"name": "Team", "members": [{"name": "The Owner", "role": "owner"}]},
        )
        result = inject_metadata(_base_yaml(), contract)
        data = yaml.safe_load(result)
        assert data["models"][0]["config"]["meta"]["owner"] == "The Owner"


class TestInjectColumnMeta:
    """Column-level metadata from schema properties."""

    def _make_column_contract(self, **prop_extras: object) -> OpenDataContractStandard:
        prop: dict = {"name": "col_a", "logicalType": "string"}
        prop.update(prop_extras)
        return OpenDataContractStandard.model_validate(
            {
                "kind": "DataContract",
                "apiVersion": "v3.1.0",
                "id": "test-meta",
                "name": "Col Contract",
                "version": "1.0.0",
                "status": "active",
                "schema": [{"name": "my_model", "physicalType": "table", "properties": [prop]}],
            },
        )

    def test_critical_data_element(self) -> None:
        """CriticalDataElement maps to column.meta.critical_data_element."""
        contract = self._make_column_contract(criticalDataElement=True)
        result = inject_metadata(_base_yaml(), contract)
        data = yaml.safe_load(result)
        col = data["models"][0]["columns"][0]
        assert col["meta"]["critical_data_element"] is True

    def test_business_name(self) -> None:
        """BusinessName maps to column.meta.business_name."""
        contract = self._make_column_contract(businessName="Annual Revenue")
        result = inject_metadata(_base_yaml(), contract)
        data = yaml.safe_load(result)
        col = data["models"][0]["columns"][0]
        assert col["meta"]["business_name"] == "Annual Revenue"

    def test_preserves_existing_meta(self) -> None:
        """Existing column meta keys are not overwritten."""
        contract = self._make_column_contract(criticalDataElement=True)
        input_yaml = yaml.safe_dump(
            {
                "version": 2,
                "models": [
                    {
                        "name": "my_model",
                        "columns": [{"name": "col_a", "meta": {"classification": "internal"}}],
                    },
                ],
            },
            sort_keys=False,
        )
        result = inject_metadata(input_yaml, contract)
        data = yaml.safe_load(result)
        col_meta = data["models"][0]["columns"][0]["meta"]
        assert col_meta["classification"] == "internal"
        assert col_meta["critical_data_element"] is True


class TestInjectDescription:
    """Rich description from contract is injected into model."""

    def test_rich_description_injected(self) -> None:
        """Structured description replaces simple model description."""
        contract = _make_contract(
            description={"purpose": "Main purpose.", "limitations": "Some limits."},
        )
        result = inject_metadata(_base_yaml(description="Old desc"), contract)
        data = yaml.safe_load(result)
        desc = data["models"][0]["description"]
        assert "Main purpose." in desc
        assert "**Limitations:** Some limits." in desc

    def test_no_description_keeps_existing(self) -> None:
        """No contract description preserves the existing model description."""
        contract = _make_contract()
        result = inject_metadata(_base_yaml(description="Keep me"), contract)
        data = yaml.safe_load(result)
        assert data["models"][0]["description"] == "Keep me"


class TestInjectNoSchema:
    """Edge case: contract without schema returns YAML unchanged."""

    def test_no_schema(self) -> None:
        """Contract with no schema returns input unchanged."""
        contract = OpenDataContractStandard.model_validate(
            {
                "kind": "DataContract",
                "apiVersion": "v3.1.0",
                "id": "empty",
                "name": "Empty",
                "version": "1.0.0",
                "status": "active",
            },
        )
        input_yaml = "version: 2\nmodels: []\n"
        assert inject_metadata(input_yaml, contract) == input_yaml
