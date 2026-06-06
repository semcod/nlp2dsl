"""Tests for workflow simulate helpers."""

from __future__ import annotations

from nlp2dsl_sdk.workflow.simulate import simulate_workflow_payload


def test_simulate_workflow_marks_side_effects() -> None:
    payload = simulate_workflow_payload(
        {
            "name": "full_report_flow",
            "steps": [
                {"action": "generate_report", "config": {"report_type": "sales", "format": "pdf"}},
                {"action": "send_email", "config": {"to": "a@b.pl", "subject": "x", "body": "y"}},
                {"action": "notify_slack", "config": {"channel": "#sales", "message": "ok"}},
            ],
        }
    )
    assert payload["stage"] == "simulate"
    assert payload["status"] == "ready"
    assert payload["step_count"] == 3
    assert payload["side_effect_count"] == 2
    assert payload["steps"][0]["side_effect"] is False
    assert payload["steps"][1]["side_effect"] is True
    assert payload["steps"][0]["preview_result"]["simulated"] is True


def test_simulate_workflow_empty_steps_not_executable() -> None:
    payload = simulate_workflow_payload({"name": "empty", "steps": []})
    assert payload["can_execute"] is False
    assert payload["status"] == "validation_failed"
