"""Tests for app.executors.router."""

from __future__ import annotations

from app.executors.router import (
    ExecutionRoute,
    execution_backend_for_intent,
    execution_backend_for_runtime,
    route_action,
    route_workflow_steps,
)


def test_execution_backend_for_runtime() -> None:
    assert execution_backend_for_runtime("executor:worker") == "worker"
    assert execution_backend_for_runtime("delegate:mullm") == "mullm"
    assert execution_backend_for_runtime("orchestrator:nlp-service") == "system"


def test_route_action_worker() -> None:
    route = route_action("send_invoice")
    assert route.backend == "worker"
    assert route.runtime_id == "executor:worker"
    assert route.delegated is False


def test_route_action_mullm() -> None:
    route = route_action("mullm_shell_task")
    assert route.backend == "mullm"
    assert route.delegated is True


def test_route_workflow_steps() -> None:
    steps = [
        {"action": "generate_report", "config": {"report_type": "sales"}},
        {"action": "send_email", "config": {"to": "a@b.pl"}},
    ]
    routes = route_workflow_steps(steps)
    assert len(routes) == 2
    assert all(isinstance(r, ExecutionRoute) for r in routes)
    assert routes[0].backend == "worker"


def test_execution_backend_for_intent_fallback() -> None:
    assert execution_backend_for_intent("send_email") == "worker"
    assert execution_backend_for_intent("mullm_shell_task") == "mullm"
