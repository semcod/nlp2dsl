"""Execute Mullm-only workflow steps via orchestrator API."""

from __future__ import annotations

import os
from typing import Any

from nlp2dsl_sdk.mullm.client import MullmClient, MullmClientError
from nlp2dsl_sdk.mullm.payloads import build_task_payload, is_mullm_action


def _workflow_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps") or []
    return [s for s in steps if isinstance(s, dict)]


def workflow_has_mullm_steps(workflow: dict[str, Any]) -> bool:
    return any(is_mullm_action(str(s.get("action") or "")) for s in _workflow_steps(workflow))


def is_mullm_only_workflow(workflow: dict[str, Any]) -> bool:
    steps = _workflow_steps(workflow)
    return bool(steps) and all(is_mullm_action(str(s.get("action") or "")) for s in steps)


def _delegate_mode() -> str:
    return (os.environ.get("MULLM_DELEGATE_MODE") or "auto").strip().lower()


def _should_simulate(client: MullmClient) -> bool:
    mode = _delegate_mode()
    if mode == "simulate":
        return True
    if mode == "live":
        return False
    return not client.ping()


def _require_mullm_only_steps(steps: list[dict[str, Any]]) -> None:
    if not steps:
        raise ValueError("workflow has no steps")
    non_mullm = [s for s in steps if not is_mullm_action(str(s.get("action") or ""))]
    if non_mullm:
        actions = ", ".join(str(s.get("action")) for s in non_mullm)
        raise ValueError(f"workflow mixes Mullm and non-Mullm steps: {actions}")


def _run_mullm_step(
    step: dict[str, Any],
    *,
    mullm: MullmClient,
    workflow_id: str,
    session_id: str | None,
    simulate: bool,
    step_index: int,
) -> dict[str, Any]:
    action = str(step.get("action") or "")
    step_id = str(step.get("id") or step.get("step_id") or f"step-{step_index}")
    payload = build_task_payload(step, workflow_id=workflow_id, session_id=session_id)
    entry: dict[str, Any] = {
        "step_id": step_id,
        "action": action,
        "status": "pending",
        "result": None,
        "error": None,
    }

    try:
        if simulate:
            entry["status"] = "completed"
            entry["result"] = mullm.simulate_task(payload)
            return entry
        api_result = mullm.create_task(payload)
        entry["status"] = "completed"
        entry["result"] = {**api_result, "transport": "mullm_api"}
        return entry
    except MullmClientError as exc:
        if _delegate_mode() == "auto" and not simulate:
            entry["status"] = "completed"
            entry["result"] = {**mullm.simulate_task(payload), "fallback_reason": str(exc)}
            return entry
        entry["status"] = "failed"
        entry["error"] = str(exc)
        return entry


def _execution_envelope(
    workflow: dict[str, Any],
    *,
    workflow_id: str,
    step_results: list[dict[str, Any]],
    simulate: bool,
) -> dict[str, Any]:
    overall = "failed" if any(s.get("status") == "failed" for s in step_results) else "completed"
    return {
        "workflow_id": workflow_id,
        "name": workflow.get("name"),
        "status": overall,
        "steps": step_results,
        "execution_backend": "mullm",
        "simulated": simulate or any(
            (r.get("result") or {}).get("transport") == "simulated" for r in step_results
        ),
    }


def execute_mullm_workflow(
    workflow: dict[str, Any],
    *,
    session_id: str | None = None,
    client: MullmClient | None = None,
) -> dict[str, Any]:
    """
    Run each Mullm step sequentially. Returns worker-shaped execution envelope.
    """
    steps = _workflow_steps(workflow)
    _require_mullm_only_steps(steps)

    mullm = client or MullmClient()
    simulate = _should_simulate(mullm)
    workflow_id = str(workflow.get("id") or workflow.get("workflow_id") or "wf")

    step_results: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        entry = _run_mullm_step(
            step,
            mullm=mullm,
            workflow_id=workflow_id,
            session_id=session_id,
            simulate=simulate,
            step_index=index,
        )
        step_results.append(entry)
        if entry["status"] == "failed":
            break

    return _execution_envelope(workflow, workflow_id=workflow_id, step_results=step_results, simulate=simulate)
