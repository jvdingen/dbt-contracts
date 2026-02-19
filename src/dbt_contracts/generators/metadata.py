"""Propagate ODCS/ODPS metadata (tags, descriptions, owner, domain) into dbt schema YAML."""

from __future__ import annotations

import logging
from typing import Any

import yaml
from open_data_contract_standard.model import Description, OpenDataContractStandard, Team, TeamMember

logger = logging.getLogger(__name__)


def _build_description(contract: OpenDataContractStandard, schema_description: str | None) -> str | None:
    """Build a rich model description from the contract-level Description object.

    Combines ``purpose``, ``limitations``, and ``usage`` fields into a single
    formatted string.  Falls back to *schema_description* when the contract
    carries no structured description.
    """
    desc: Description | None = contract.description
    if desc is None:
        return schema_description

    parts: list[str] = []
    if desc.purpose:
        parts.append(desc.purpose)
    if desc.limitations:
        parts.append(f"**Limitations:** {desc.limitations}")
    if desc.usage:
        parts.append(f"**Usage:** {desc.usage}")

    if not parts:
        return schema_description

    return "\n\n".join(parts)


def _resolve_owner(team: Team | list[TeamMember] | None) -> str | None:
    """Extract an owner name from the contract ``team`` field.

    Handles both union variants accepted by the ODCS spec:
    * ``Team`` object — prefer the member whose ``role`` is ``"owner"``,
      fall back to ``team.name``.
    * ``list[TeamMember]`` — find the member with ``role="owner"``.
    """
    if team is None:
        return None

    if isinstance(team, list):
        # bare list[TeamMember]
        for member in team:
            if member.role == "owner" and member.name:
                return member.name
        return None

    # Team object
    if team.members:
        for member in team.members:
            if member.role == "owner" and member.name:
                return member.name
    return team.name


def inject_metadata(
    model_yaml: str,
    contract: OpenDataContractStandard,
    product_tags: list[str] | None = None,
    product_domain: str | None = None,
) -> str:
    """Inject contract/product metadata into an exported dbt model YAML string.

    Merges tags, enriches descriptions, and adds ``config.meta`` entries for
    owner, domain, and column-level fields (``criticalDataElement``,
    ``businessName``).
    """
    if not contract.schema_:
        return model_yaml

    data = yaml.safe_load(model_yaml)
    if not data or "models" not in data:
        return model_yaml

    # Collect tags from contract + product
    all_tags: list[str] = []
    if contract.tags:
        all_tags.extend(contract.tags)
    if product_tags:
        all_tags.extend(product_tags)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in all_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    owner = _resolve_owner(contract.team)

    for model in data["models"]:
        model_name = model.get("name")

        # Find matching schema object
        schema_obj = next(
            (s for s in contract.schema_ if getattr(s, "name", None) == model_name),
            None,
        )
        if schema_obj is None:
            logger.debug("Skipping model '%s': no matching schema object in contract '%s'", model_name, contract.id or "<unknown>")
            continue

        logger.debug("Injecting metadata into model '%s' (contract '%s')", model_name, contract.id or "<unknown>")

        # --- Tags ---
        if unique_tags:
            existing_tags: list[str] = model.get("tags", [])
            merged_seen: set[str] = set(existing_tags)
            merged_tags = list(existing_tags)
            for tag in unique_tags:
                if tag not in merged_seen:
                    merged_seen.add(tag)
                    merged_tags.append(tag)
            model["tags"] = merged_tags

        # --- Description ---
        schema_desc = model.get("description")
        rich_desc = _build_description(contract, schema_desc)
        if rich_desc:
            model["description"] = rich_desc

        # --- Model-level meta (owner, domain) ---
        meta: dict[str, Any] = {}
        if owner:
            meta["owner"] = owner
        if product_domain:
            meta["domain"] = product_domain

        if meta:
            model.setdefault("config", {})
            existing_meta: dict[str, Any] = model["config"].get("meta", {})
            existing_meta.update(meta)
            model["config"]["meta"] = existing_meta

        # --- Column-level meta ---
        properties = getattr(schema_obj, "properties", None) or []
        columns: list[dict[str, Any]] = model.get("columns", [])
        for prop in properties:
            prop_name = getattr(prop, "name", None)
            if not prop_name:
                continue

            col = next((c for c in columns if c.get("name") == prop_name), None)
            if col is None:
                continue

            col_meta: dict[str, Any] = {}
            if getattr(prop, "criticalDataElement", None) is not None:
                col_meta["critical_data_element"] = prop.criticalDataElement
            if getattr(prop, "businessName", None) is not None:
                col_meta["business_name"] = prop.businessName

            if col_meta:
                existing_col_meta: dict[str, Any] = col.get("meta", {})
                existing_col_meta.update(col_meta)
                col["meta"] = existing_col_meta

    return yaml.safe_dump(data, sort_keys=False)
