"""Delegacja wykonania workflow do Mullm BFF vs worker lokalny."""

from __future__ import annotations

from typing import Any

from app.registry import DELEGATED_ACTIONS, MULLM_ACTIONS


def is_delegated_to_mullm(intent: str | None) -> bool:
    return bool(intent and intent in DELEGATED_ACTIONS)


def execution_backend_for_intent(intent: str | None) -> str:
    """Backend wykonania DSL: mullm | worker."""
    return "mullm" if is_delegated_to_mullm(intent) else "worker"


def mullm_action_names() -> frozenset[str]:
    return frozenset(MULLM_ACTIONS)


def delegate_payload(action: str, config: dict[str, Any]) -> dict[str, Any]:
    """Kontrakt dla Mullm conductor._ready_action_payload."""
    return {
        "action": action,
        "config": config,
        "backend": "mullm",
    }
