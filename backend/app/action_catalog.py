"""Action catalog — proxy nlp-service /nlp/actions (C1)."""

from __future__ import annotations

import os
from typing import Any

from httpx import AsyncClient, Client

from app.schemas import ActionInfo
from dsl_contracts import (
    action_contracts_from_catalog,
    action_info_config_schema,
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


def _default_nlp_service_url() -> str:
    return os.getenv("NLP_SERVICE_URL", "http://nlp-service:8012").rstrip("/")


def nlp_actions_to_action_info(payload: dict[str, Any]) -> list[ActionInfo]:
    """Convert nlp-service /nlp/actions dict → backend ActionInfo list."""
    actions: list[ActionInfo] = []
    for name, contract in action_contracts_from_catalog(payload).items():
        actions.append(
            ActionInfo(
                name=name,
                description=contract.description or name,
                config_schema=action_info_config_schema(contract),
            )
        )
    return actions


async def fetch_action_catalog(
    nlp_service_url: str,
    *,
    client: AsyncClient | None = None,
    timeout: float = 10.0,
) -> list[ActionInfo]:
    """Fetch action vocabulary from nlp-service."""
    url = f"{nlp_service_url.rstrip('/')}/nlp/actions"
    if client is not None:
        resp = await client.get(url, timeout=timeout)
    else:
        async with AsyncClient(timeout=timeout) as owned:
            resp = await owned.get(url)
    resp.raise_for_status()
    payload = resp.json()
    if not isinstance(payload, dict):
        return []
    return nlp_actions_to_action_info(payload)


def load_action_field_catalog(
    *,
    nlp_service_url: str | None = None,
    force: bool = False,
) -> dict[str, dict[str, Any]]:
    """Sync cache of /nlp/actions for step validation (fallback when nlp-service offline)."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None and not force:
        return _CATALOG_CACHE

    url = f"{(nlp_service_url or _default_nlp_service_url()).rstrip('/')}/nlp/actions"
    try:
        with Client(timeout=2.0) as client:
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
