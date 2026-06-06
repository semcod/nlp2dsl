"""Action field catalog from nlp-service /nlp/actions (B1/C1)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from dsl_contracts import (
    known_action_names,
    quality_fields_for_action as contract_quality_fields_for_action,
    required_fields_for_action as contract_required_fields_for_action,
)

_FALLBACK_ACTION_FIELDS: dict[str, dict[str, list[str]]] = {
    "send_invoice": {"required": ["amount", "to"], "quality_required": []},
    "generate_invoice": {"required": ["amount", "to"], "quality_required": []},
    "send_email": {
        "required": ["to"],
        "quality_required": ["body"],
    },
    "generate_report": {"required": ["report_type"], "quality_required": []},
    "notify_slack": {"required": ["channel"], "quality_required": ["message"]},
    "notify_telegram": {"required": ["chat_id"], "quality_required": ["message"]},
    "notify_teams": {"required": ["channel"], "quality_required": ["message"]},
}

_CATALOG_CACHE: dict[str, Any] | None = None
_CATALOG_TIMEOUT_SECONDS = float(os.getenv("WORKER_CATALOG_TIMEOUT", "5"))


def _default_nlp_service_url() -> str:
    return os.getenv("NLP_SERVICE_URL", "http://nlp-service:8002").rstrip("/")


def load_action_field_catalog(
    *,
    nlp_service_url: str | None = None,
    force: bool = False,
    timeout: float = _CATALOG_TIMEOUT_SECONDS,
) -> dict[str, dict[str, Any]]:
    """Sync cache of /nlp/actions for worker validation (fallback when offline)."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not force:
        return _CATALOG_CACHE

    url = f"{(nlp_service_url or _default_nlp_service_url()).rstrip('/')}/nlp/actions"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict):
                _CATALOG_CACHE = payload
                return payload
    except Exception:
        pass

    _CATALOG_CACHE = dict(_FALLBACK_ACTION_FIELDS)
    return _CATALOG_CACHE


def required_fields_for_action(action: str, *, catalog: dict[str, Any] | None = None) -> list[str]:
    return contract_required_fields_for_action(action, catalog=catalog or load_action_field_catalog())


def quality_fields_for_action(action: str, *, catalog: dict[str, Any] | None = None) -> list[str]:
    return contract_quality_fields_for_action(action, catalog=catalog or load_action_field_catalog())


def known_action_names_from_catalog(*, catalog: dict[str, Any] | None = None) -> frozenset[str]:
    return known_action_names(catalog=catalog or load_action_field_catalog())
