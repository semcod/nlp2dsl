"""Tests for persisted workflow lifecycle events."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.memory import MemoryWorkflowRepo
from app.engine import _publish_workflow_event
from app.main import app


@pytest.mark.asyncio
async def test_memory_repo_append_and_list_events() -> None:
    repo = MemoryWorkflowRepo()
    await repo.append_event(
        "wf1",
        {"event_id": "e1", "event_type": "WorkflowCreated", "workflow_id": "wf1", "status": "running"},
    )
    await repo.append_event(
        "wf1",
        {"event_id": "e2", "event_type": "StepExecuted", "workflow_id": "wf1", "status": "running"},
    )
    events = await repo.list_events("wf1")
    assert len(events) == 2
    assert events[0]["event_id"] == "e1"
    assert events[1]["event_type"] == "StepExecuted"


@pytest.mark.asyncio
async def test_publish_workflow_event_persists_canonical_payload() -> None:
    repo = MemoryWorkflowRepo()
    with patch("app.engine._repo", repo), patch("app.engine.get_request_id", return_value="corr-1"):
        await _publish_workflow_event(
            "wf-events",
            "step_completed",
            "running",
            "step ok",
            step_id="s1",
            action="send_email",
            step_index=1,
            total_steps=1,
            payload={"result": {"ok": True}},
        )

    events = await repo.list_events("wf-events")
    assert len(events) == 1
    assert events[0]["event_type"] == "StepExecuted"
    assert events[0]["legacy_event_type"] == "step_completed"
    assert events[0]["correlation_id"] == "corr-1"


@pytest.mark.asyncio
async def test_get_workflow_events_endpoint() -> None:
    repo = MemoryWorkflowRepo()
    await repo.save_run("wf-api", "demo", "completed", {"trigger": "manual", "steps": []})
    await repo.append_event(
        "wf-api",
        {
            "event_id": "e1",
            "workflow_id": "wf-api",
            "event_type": "WorkflowCreated",
            "status": "running",
            "message": "start",
        },
    )
    await repo.append_event(
        "wf-api",
        {
            "event_id": "e2",
            "workflow_id": "wf-api",
            "event_type": "WorkflowCompleted",
            "status": "completed",
            "message": "done",
            "terminal": True,
        },
    )

    with patch("app.routers.workflow._repo", repo), patch("app.engine._repo", repo):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/workflow/history/wf-api/events")

    assert resp.status_code == 200
    body = resp.json()
    assert body["workflow_id"] == "wf-api"
    assert body["count"] == 2
    assert body["reconstructed"]["status"] == "completed"


@pytest.mark.asyncio
async def test_get_workflow_events_not_found() -> None:
    repo = MemoryWorkflowRepo()
    with patch("app.routers.workflow._repo", repo):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/workflow/history/missing/events")
    assert resp.status_code == 404
