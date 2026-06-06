"""Tests for shared idempotent workflow execution."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.idempotency import MemoryIdempotencyStore
from app.workflow_execute import (
    derive_chat_idempotency_key,
    resolve_idempotency_key,
    run_idempotent_workflow,
    workflow_has_side_effects,
)


def test_workflow_has_side_effects_detects_send_email() -> None:
    workflow = {
        "name": "auto_send_email",
        "steps": [{"action": "send_email", "config": {"to": "a@b.pl"}}],
    }
    assert workflow_has_side_effects(workflow) is True


def test_workflow_has_side_effects_ignores_generate_report() -> None:
    workflow = {
        "name": "auto_generate_report",
        "steps": [{"action": "generate_report", "config": {"report_type": "sales"}}],
    }
    assert workflow_has_side_effects(workflow) is False


def test_resolve_idempotency_key_prefers_explicit_value() -> None:
    workflow = {"name": "wf", "steps": [{"action": "send_email", "config": {}}]}
    assert (
        resolve_idempotency_key(
            explicit_key="client-key",
            workflow=workflow,
            conversation_id="conv-1",
        )
        == "client-key"
    )


def test_resolve_idempotency_key_derives_from_chat_conversation() -> None:
    workflow = {"name": "wf", "steps": [{"action": "send_invoice", "config": {}}]}
    key = resolve_idempotency_key(
        explicit_key=None,
        workflow=workflow,
        conversation_id="conv-abc",
    )
    assert key == derive_chat_idempotency_key("conv-abc", workflow)


@pytest.mark.asyncio
async def test_run_idempotent_workflow_replays_cached_result() -> None:
    workflow = {
        "name": "auto_send_invoice",
        "steps": [{"action": "send_invoice", "config": {"amount": 100, "to": "a@b.pl"}}],
    }
    store = MemoryIdempotencyStore()
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "workflow_id": "wf-1",
        "status": "completed",
        "steps": [],
    }

    with patch("app.workflow_execute.idempotency_store", store), patch(
        "app.workflow_execute.run_workflow", AsyncMock(return_value=mock_result)
    ) as run_workflow:
        first = await run_idempotent_workflow(workflow, idempotency_key="idem-1")
        second = await run_idempotent_workflow(workflow, idempotency_key="idem-1")

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["result"]["workflow_id"] == "wf-1"
    run_workflow.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_idempotent_workflow_routes_mullm_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MULLM_DELEGATE_MODE", "simulate")
    workflow = {
        "name": "shell",
        "steps": [{"action": "mullm_shell_task", "config": {"shell_command": "true"}}],
    }
    run_workflow = AsyncMock()

    with patch("app.workflow_execute.run_workflow", run_workflow):
        payload = await run_idempotent_workflow(workflow)

    run_workflow.assert_not_awaited()
    assert payload["result"]["execution_backend"] == "mullm"
    assert payload["result"]["simulated"] is True


@pytest.mark.asyncio
async def test_run_idempotent_workflow_executes_without_key() -> None:
    workflow = {"name": "wf", "steps": [{"action": "generate_report", "config": {}}]}
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {"workflow_id": "wf-live", "status": "completed"}

    with patch("app.workflow_execute.run_workflow", AsyncMock(return_value=mock_result)) as run_workflow:
        payload = await run_idempotent_workflow(workflow)

    assert payload["idempotency_key"] is None
    assert payload["idempotent_replay"] is False
    assert payload["result"]["workflow_id"] == "wf-live"
    run_workflow.assert_awaited_once()
    mock_result.model_dump.assert_called_once_with(mode="json")
