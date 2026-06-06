"""Tests for canonical workflow lifecycle events."""

from __future__ import annotations

from nlp2dsl_sdk.workflow.events import (
    lifecycle_event_from_payload,
    normalize_event_type,
    workflow_snapshot_from_events,
)


def test_normalize_event_type_maps_legacy_names() -> None:
    assert normalize_event_type("workflow_started") == "WorkflowCreated"
    assert normalize_event_type("step_completed") == "StepExecuted"
    assert normalize_event_type("workflow_failed") == "ExecutionFailed"


def test_lifecycle_event_from_payload_adds_correlation_id() -> None:
    event = lifecycle_event_from_payload(
        {
            "event_id": "e1",
            "workflow_id": "wf1",
            "event_type": "step_started",
            "status": "running",
            "message": "step go",
            "step_id": "s1",
            "action": "send_email",
        },
        correlation_id="req-abc",
    )
    assert event.event_type == "StepExecutionRequested"
    assert event.legacy_event_type == "step_started"
    assert event.correlation_id == "req-abc"


def test_workflow_snapshot_from_events_completed() -> None:
    events = [
        lifecycle_event_from_payload(
            {
                "event_id": "e1",
                "workflow_id": "wf1",
                "event_type": "workflow_started",
                "status": "running",
                "message": "start",
            }
        ),
        lifecycle_event_from_payload(
            {
                "event_id": "e2",
                "workflow_id": "wf1",
                "event_type": "step_completed",
                "status": "running",
                "message": "done step",
                "step_id": "s1",
            }
        ),
        lifecycle_event_from_payload(
            {
                "event_id": "e3",
                "workflow_id": "wf1",
                "event_type": "workflow_completed",
                "status": "completed",
                "message": "all done",
            }
        ),
    ]
    snapshot = workflow_snapshot_from_events(events)
    assert snapshot["status"] == "completed"
    assert snapshot["steps_completed"] == 1
    assert snapshot["terminal_event_type"] == "WorkflowCompleted"


def test_workflow_snapshot_from_events_failed_step() -> None:
    events = [
        lifecycle_event_from_payload(
            {
                "event_id": "e1",
                "workflow_id": "wf2",
                "event_type": "workflow_started",
                "status": "running",
                "message": "start",
            }
        ),
        lifecycle_event_from_payload(
            {
                "event_id": "e2",
                "workflow_id": "wf2",
                "event_type": "step_failed",
                "status": "failed",
                "message": "boom",
                "step_id": "s1",
            }
        ),
        lifecycle_event_from_payload(
            {
                "event_id": "e3",
                "workflow_id": "wf2",
                "event_type": "workflow_failed",
                "status": "failed",
                "message": "stopped",
            }
        ),
    ]
    snapshot = workflow_snapshot_from_events(events)
    assert snapshot["status"] == "failed"
    assert snapshot["terminal_event_type"] == "ExecutionFailed"
