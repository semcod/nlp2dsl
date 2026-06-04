"""
Ładowanie rejestrów akcji z pluginów integrations/*.

Użycie przy starcie nlp-service:
  INTEGRATIONS=mullm  (domyślnie: mullm)
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import Any

log = logging.getLogger("integrations")


def _integration_names() -> list[str]:
    raw = os.getenv("INTEGRATIONS", "mullm").strip()
    if not raw or raw.lower() in {"none", "off", "0"}:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def load_integration_registries() -> dict[str, dict[str, Any]]:
    """Zwraca {nazwa_pluginu: {action_name: meta}}."""
    out: dict[str, dict[str, Any]] = {}
    for name in _integration_names():
        try:
            mod = importlib.import_module(f"integrations.{name}.registry")
        except ImportError as exc:
            log.warning("Integration %s skipped: %s", name, exc)
            continue
        actions = getattr(mod, f"{name.upper()}_ACTIONS", None) or getattr(
            mod, "ACTIONS", None
        )
        if not isinstance(actions, dict):
            log.warning("Integration %s has no ACTIONS dict", name)
            continue
        out[name] = actions
        log.info("Loaded integration %s (%d actions)", name, len(actions))
    return out


def apply_integrations(registry: dict[str, dict[str, Any]]) -> set[str]:
    """
    Merge pluginów do ACTIONS_REGISTRY.
    Zwraca zbiór nazw akcji z category=mullm.
    """
    delegated: set[str] = set()
    for plugin_name, actions in load_integration_registries().items():
        for action_name, meta in actions.items():
            if action_name in registry:
                log.warning(
                    "Action %s from %s overwrites existing registry entry",
                    action_name,
                    plugin_name,
                )
            registry[action_name] = {**meta, "plugin": plugin_name}
            if meta.get("category") == "mullm":
                delegated.add(action_name)
    return delegated
