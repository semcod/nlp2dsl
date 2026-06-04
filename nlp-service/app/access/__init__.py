"""Konfiguracja zasobów i kontrola dostępu (nlp2dsl.yaml)."""

from app.access.config import get_access_config, reload_access_config
from app.access.native import resolve_native_intent
from app.access.policy import authorize_action, get_agent_id
from app.access.bootstrap import bootstrap_registry

__all__ = [
    "bootstrap_registry",
    "get_access_config",
    "reload_access_config",
    "resolve_native_intent",
    "authorize_action",
    "get_agent_id",
]
