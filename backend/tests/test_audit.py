"""Tests for workflow audit read-model."""

from __future__ import annotations

import pytest

from app.audit import build_audit_entries
from app.db.memory import MemoryWorkflowRepo


@pytest.mark.asyncio
async def test_build_audit_entries_lists_runs_with_actions() -> None:
    repo = MemoryWorkflowRepo()
    await repo.save_run(
        "wf-1",
        "invoice_flow",
        "completed",
        {
            "trigger": "manual",
            "steps": [{"action": "send_invoice", "status": "completed", "result": {}}],
        },
    )
    await repo.append_event("wf-1", {"event_type": "WorkflowCompleted", "workflow_id": "wf-1"})

    payload = await build_audit_entries(repo, limit=10)
    assert payload["count"] == 1
    assert payload["entries"][0]["workflow_id"] == "wf-1"
    assert payload["entries"][0]["actions"] == ["send_invoice"]
    assert "WorkflowCompleted" in payload["entries"][0]["event_types"]


@pytest.mark.asyncio
async def test_build_audit_entries_filters_by_action() -> None:
    repo = MemoryWorkflowRepo()
    await repo.save_run(
        "wf-a",
        "email",
        "completed",
        {"steps": [{"action": "send_email", "status": "completed"}]},
    )
    await repo.save_run(
        "wf-b",
        "invoice",
        "completed",
        {"steps": [{"action": "send_invoice", "status": "completed"}]},
    )

    payload = await build_audit_entries(repo, action="send_invoice")
    assert payload["count"] == 1
    assert payload["entries"][0]["workflow_id"] == "wf-b"
