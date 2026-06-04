"""Natywne trasy z nlp2dsl.yaml — przed parserem rules/LLM."""

from __future__ import annotations

import re
from typing import Any

from app.access.config import get_access_config


def _match_route(text: str, route: dict[str, Any]) -> bool:
    text_lower = text.lower().strip()
    patterns = route.get("patterns") or []
    for pat in patterns:
        if not isinstance(pat, dict):
            continue
        ptype = (pat.get("type") or "substring").lower()
        if ptype == "regex":
            rx = pat.get("value") or pat.get("pattern") or ""
            if rx and re.search(rx, text_lower, re.IGNORECASE):
                return True
        elif ptype == "keywords":
            keywords = pat.get("keywords") or []
            if all(kw.lower() in text_lower for kw in keywords):
                return True
        else:
            sub = pat.get("value") or pat.get("substring") or ""
            if sub and sub.lower() in text_lower:
                return True
    aliases = route.get("aliases") or []
    for alias in aliases:
        if str(alias).lower() in text_lower:
            return True
    return False


def resolve_native_intent(text: str) -> dict[str, Any] | None:
    """
    Zwraca {action, resource_area?, permission_action?, uri?} lub None.
    """
    if not (text or "").strip():
        return None
    cfg = get_access_config()
    action_areas = cfg.action_to_area()

    for route in cfg.native_routes:
        action = route.get("action") or route.get("intent")
        if not action or not _match_route(text, route):
            continue
        area = route.get("resource_area") or action_areas.get(str(action))
        return {
            "action": str(action),
            "resource_area": area,
            "permission_action": route.get("permission_action", "execute"),
            "uri": route.get("uri"),
            "source": "native_routing",
        }

    # Domyślna trasa: akcje z YAML resource_areas (aliasy w actions)
    from app.registry import ACTIONS_REGISTRY

    text_lower = text.lower()
    best: tuple[str, int] | None = None
    for action_name, meta in ACTIONS_REGISTRY.items():
        if meta.get("native_route") is False:
            continue
        for alias in meta.get("aliases") or []:
            if alias.lower() in text_lower:
                length = len(alias)
                if best is None or length > best[1]:
                    best = (action_name, length)
    if best:
        action_name = best[0]
        meta = ACTIONS_REGISTRY.get(action_name, {})
        return {
            "action": action_name,
            "resource_area": meta.get("resource_area"),
            "permission_action": meta.get("permission_action", "execute"),
            "uri": meta.get("resource_uri"),
            "source": "action_aliases",
        }
    return None
