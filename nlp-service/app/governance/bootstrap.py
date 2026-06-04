"""Scala rejestr akcji: core + integracje (z YAML) + resource_areas z YAML."""

from __future__ import annotations

import logging
from typing import Any

from app.governance.config import get_access_config

log = logging.getLogger("access.bootstrap")


def _actions_from_yaml_areas() -> dict[str, dict[str, Any]]:
    cfg = get_access_config()
    out: dict[str, dict[str, Any]] = {}
    for area in cfg.resource_areas:
        area_id = area.get("id") or area.get("area_id") or ""
        actions = area.get("actions") or {}
        if not isinstance(actions, dict):
            continue
        for action_name, spec in actions.items():
            if not isinstance(spec, dict):
                continue
            meta = {
                "description": spec.get("description", action_name),
                "required": list(spec.get("required") or []),
                "optional": dict(spec.get("optional") or {}),
                "aliases": list(spec.get("aliases") or []),
                "param_aliases": dict(spec.get("param_aliases") or {}),
                "category": spec.get("category", area.get("connector", "delegate")),
                "execution": spec.get("execution", "delegate"),
                "resource_area": area_id,
                "permission_action": spec.get("permission_action", "execute"),
                "resource_uri": spec.get("resource_uri"),
                "uri_patterns": list(area.get("uri_patterns") or []),
                "labels": list(area.get("labels") or []),
                "plugin": "nlp2dsl.yaml",
                "native_route": spec.get("native_route", True),
            }
            out[action_name] = meta
    return out


def apply_yaml_actions(registry: dict[str, dict[str, Any]]) -> set[str]:
    """Merge akcji z resource_areas; zwraca zbiór akcji delegowanych."""
    delegated: set[str] = set()
    for action_name, meta in _actions_from_yaml_areas().items():
        registry[action_name] = meta
        cat = meta.get("category", "")
        ex = meta.get("execution", "")
        if cat in ("mullm", "delegate", "external") or ex == "delegate":
            delegated.add(action_name)
    return delegated


def bootstrap_registry(
    registry: dict[str, dict[str, Any]],
) -> tuple[set[str], set[str]]:
    """
    Zwraca (MULLM_ACTIONS, DELEGATED_ACTIONS).
    """
    from integrations.loader import apply_integrations

    cfg = get_access_config()
    import os

    os.environ["INTEGRATIONS"] = ",".join(cfg.enabled_integrations)

    mullm = apply_integrations(registry)
    delegated = apply_yaml_actions(registry)
    all_delegated = mullm | delegated
    log.info(
        "Registry bootstrap: %d actions, %d delegated (integrations=%s)",
        len(registry),
        len(all_delegated),
        cfg.enabled_integrations,
    )
    return mullm, all_delegated
