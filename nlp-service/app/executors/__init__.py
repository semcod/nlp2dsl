"""Execution routing — worker, Mullm delegate, or local system executor."""

from app.executors.router import (
    ExecutionRoute,
    delegate_payload,
    execution_backend_for_intent,
    execution_backend_for_runtime,
    is_delegated_to_mullm,
    route_action,
)

__all__ = [
    "ExecutionRoute",
    "delegate_payload",
    "execution_backend_for_intent",
    "execution_backend_for_runtime",
    "is_delegated_to_mullm",
    "route_action",
]
