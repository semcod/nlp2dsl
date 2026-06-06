"""Canonical workflow lifecycle events for audit and replay."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field

CanonicalEventType = Literal[
    "WorkflowCreated",
    "StepPlanned",
    "StepValidated",
    "AwaitingUserInput",
    "StepExecutionRequested",
    "StepExecuted",
    "ExecutionFailed",
    "WorkflowCompleted",
]

CANONICAL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "WorkflowCreated",
        "StepPlanned",
        "StepValidated",
        "AwaitingUserInput",
        "StepExecutionRequested",
        "StepExecuted",
        "ExecutionFailed",
        "WorkflowCompleted",
    }
)

TERMINAL_CANONICAL_TYPES: frozenset[str] = frozenset({"WorkflowCompleted", "ExecutionFailed"})

LEGACY_TO_CANONICAL: dict[str, str] = {
    "workflow_started": "WorkflowCreated",
    "workflow_created": "WorkflowCreated",
    "step_planned": "StepPlanned",
    "step_validated": "StepValidated",
    "awaiting_user_input": "AwaitingUserInput",
    "step_started": "StepExecutionRequested",
    "step_execution_requested": "StepExecutionRequested",
    "step_completed": "StepExecuted",
    "step_executed": "StepExecuted",
    "step_failed": "ExecutionFailed",
    "workflow_failed": "ExecutionFailed",
    "execution_failed": "ExecutionFailed",
    "workflow_completed": "WorkflowCompleted",
}


class WorkflowLifecycleEvent(BaseModel):
    """Normalized audit event persisted alongside workflow runs."""

    event_id: str
    workflow_id: str
    event_type: CanonicalEventType | str
    legacy_event_type: str | None = None
    status: str
    message: str
    step_id: str | None = None
    action: str | None = None
    step_index: int | None = None
    total_steps: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    created_at: str | None = None
    terminal: bool = False


def normalize_event_type(event_type: str) -> str:
    """Map legacy snake_case engine events to canonical PascalCase types."""
    raw = str(event_type or "").strip()
    if raw in CANONICAL_EVENT_TYPES:
        return raw
    return LEGACY_TO_CANONICAL.get(raw, raw)


def lifecycle_event_from_payload(
    payload: Mapping[str, Any],
    *,
    correlation_id: str | None = None,
) -> WorkflowLifecycleEvent:
    """Build a canonical lifecycle event from a backend event dict."""
    legacy = str(payload.get("event_type") or payload.get("legacy_event_type") or "")
    canonical = normalize_event_type(legacy)
    return WorkflowLifecycleEvent(
        event_id=str(payload.get("event_id") or ""),
        workflow_id=str(payload.get("workflow_id") or ""),
        event_type=canonical,
        legacy_event_type=legacy or None,
        status=str(payload.get("status") or ""),
        message=str(payload.get("message") or ""),
        step_id=payload.get("step_id"),
        action=payload.get("action"),
        step_index=payload.get("step_index"),
        total_steps=payload.get("total_steps"),
        payload=dict(payload.get("payload") or {}),
        correlation_id=correlation_id or payload.get("correlation_id"),
        created_at=payload.get("created_at"),
        terminal=canonical in TERMINAL_CANONICAL_TYPES or bool(payload.get("terminal")),
    )


def _normalize_lifecycle_events(
    events: Sequence[WorkflowLifecycleEvent | Mapping[str, Any]],
) -> list[WorkflowLifecycleEvent]:
    return [
        event if isinstance(event, WorkflowLifecycleEvent) else lifecycle_event_from_payload(event)
        for event in events
    ]


def _snapshot_status(
    normalized: Sequence[WorkflowLifecycleEvent],
    *,
    terminal: WorkflowLifecycleEvent | None,
    last: WorkflowLifecycleEvent,
) -> str:
    if terminal:
        return "completed" if terminal.event_type == "WorkflowCompleted" else "failed"
    if any(e.event_type == "StepExecutionRequested" for e in normalized):
        return "running"
    return last.status or "unknown"


def workflow_snapshot_from_events(
    events: Sequence[WorkflowLifecycleEvent | Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Reconstruct workflow status from persisted lifecycle events.

    Uses the latest terminal event when present; otherwise derives running state
    from the most recent step-level events.
    """
    normalized = _normalize_lifecycle_events(events)
    if not normalized:
        return {"status": "unknown", "steps_completed": 0, "last_event": None}

    last = normalized[-1]
    terminal = next((e for e in reversed(normalized) if e.terminal), None)
    return {
        "workflow_id": last.workflow_id,
        "status": _snapshot_status(normalized, terminal=terminal, last=last),
        "steps_completed": sum(1 for e in normalized if e.event_type == "StepExecuted"),
        "steps_failed": sum(1 for e in normalized if e.event_type == "ExecutionFailed" and e.step_id),
        "last_event_type": last.event_type,
        "last_event_id": last.event_id,
        "terminal_event_type": terminal.event_type if terminal else None,
        "correlation_ids": sorted({e.correlation_id for e in normalized if e.correlation_id}),
    }
