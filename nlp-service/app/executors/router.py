"""Unified execution router for DSL actions (worker | mullm | system)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.registry import DELEGATED_ACTIONS, MULLM_ACTIONS

ExecutionBackend = Literal["worker", "mullm", "system"]


@dataclass(frozen=True)
class ExecutionRoute:
    """Resolved execution target for a single DSL step."""

    action: str
    backend: ExecutionBackend
    runtime_id: str | None = None
    delegated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "backend": self.backend,
            "runtime_id": self.runtime_id,
            "delegated": self.delegated,
        }


def is_delegated_to_mullm(intent: str | None) -> bool:
    return bool(intent and intent in DELEGATED_ACTIONS)


def execution_backend_for_runtime(runtime_id: str | None) -> ExecutionBackend:
    if not runtime_id:
        return "worker"
    if runtime_id == "delegate:mullm":
        return "mullm"
    if runtime_id == "orchestrator:nlp-service":
        return "system"
    return "worker"


def execution_backend_for_intent(intent: str | None) -> ExecutionBackend:
    from app.conversation.system_map import get_doql_context, runtime_id_for_action

    if intent:
        ctx = get_doql_context()
        if ctx is not None:
            runtime_id = runtime_id_for_action(intent)
            if runtime_id:
                return execution_backend_for_runtime(runtime_id)
    return "mullm" if is_delegated_to_mullm(intent) else "worker"


def route_action(action: str, *, runtime_id: str | None = None) -> ExecutionRoute:
    """Resolve execution backend for an action name."""
    if runtime_id:
        backend = execution_backend_for_runtime(runtime_id)
    else:
        backend = execution_backend_for_intent(action)
        runtime_id = _default_runtime_for_backend(backend)
    return ExecutionRoute(
        action=action,
        backend=backend,
        runtime_id=runtime_id,
        delegated=backend == "mullm",
    )


def route_workflow_steps(steps: list[dict[str, Any]]) -> list[ExecutionRoute]:
    """Resolve routes for all steps in a workflow DSL."""
    routes: list[ExecutionRoute] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "")
        if not action:
            continue
        routes.append(route_action(action))
    return routes


def mullm_action_names() -> frozenset[str]:
    return frozenset(MULLM_ACTIONS)


def delegate_payload(action: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": action,
        "config": config,
        "backend": "mullm",
    }


def _default_runtime_for_backend(backend: ExecutionBackend) -> str | None:
    if backend == "mullm":
        return "delegate:mullm"
    if backend == "system":
        return "orchestrator:nlp-service"
    return "executor:worker"
