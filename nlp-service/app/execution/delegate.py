"""Backward-compatible shim — prefer app.executors.router."""

from app.executors.router import (
    delegate_payload,
    execution_backend_for_intent,
    execution_backend_for_runtime,
    is_delegated_to_mullm,
    mullm_action_names,
    route_action,
    route_workflow_steps,
)

__all__ = [
    "delegate_payload",
    "execution_backend_for_intent",
    "execution_backend_for_runtime",
    "is_delegated_to_mullm",
    "mullm_action_names",
    "route_action",
    "route_workflow_steps",
]
