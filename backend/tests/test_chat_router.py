"""Tests for backend chat auto-execute routing helpers."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.routers import chat


class DummyWorkflowResult:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self) -> dict[str, Any]:
        return self._payload


@pytest.mark.asyncio
async def test_ready_chat_auto_executes_worker_workflow() -> None:
    wf_payload = {
        "workflow_id": "wf-chat-1",
        "name": "invoice_chat",
        "status": "completed",
        "steps": [],
    }
    result = {
        "status": "ready",
        "auto_execute": True,
        "message": "Gotowe. Wyślij 'uruchom' aby wykonać.",
        "dsl": {
            "name": "invoice_chat",
            "trigger": "manual",
            "steps": [
                {
                    "action": "send_invoice",
                    "config": {"to": "client@example.com", "amount": 1500},
                }
            ],
        },
    }

    run_workflow = AsyncMock(return_value=DummyWorkflowResult(wf_payload))
    with patch("app.routers.chat.run_idempotent_workflow", AsyncMock(return_value={
        "result": wf_payload,
        "idempotency_key": None,
        "idempotent_replay": False,
    })) as run_idempotent:
        executed = await chat._maybe_auto_execute(result, {"text": "", "sync_auto_execute": True})

    assert executed["status"] == "executed"
    assert executed["execution_backend"] == "worker"
    assert executed["execution"] == wf_payload
    assert executed["message"] == "Gotowe. Wykonano automatycznie (sync_auto_execute)."

    run_idempotent.assert_awaited_once()
    assert run_idempotent.await_args.kwargs["idempotency_key"] is None


@pytest.mark.asyncio
async def test_ready_chat_delegates_mullm_steps_without_worker_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MULLM_DELEGATE_MODE", "simulate")
    result = {
        "status": "ready",
        "dsl": {
            "name": "list_files",
            "steps": [
                {
                    "action": "mullm_shell_task",
                    "config": {"shell_command": "ls -la"},
                }
            ],
        },
    }

    run_workflow = AsyncMock()
    with patch("app.routers.chat.run_idempotent_workflow", run_workflow):
        delegated = await chat._maybe_auto_execute(result, {"text": "uruchom"})

    run_workflow.assert_not_awaited()
    assert delegated["status"] == "executed"
    assert delegated["execution_backend"] == "mullm"
    assert delegated["execution"]["status"] == "completed"
    assert delegated["execution"]["steps"][0]["action"] == "mullm_shell_task"
    assert delegated["execution"]["steps"][0]["result"]["transport"] == "simulated"


@pytest.mark.asyncio
async def test_ready_chat_replays_uruchom_with_conversation_id() -> None:
    wf_payload = {
        "workflow_id": "wf-chat-repeat",
        "name": "invoice_chat",
        "status": "completed",
        "steps": [],
    }
    result = {
        "status": "ready",
        "conversation_id": "conv-repeat-1",
        "dsl": {
            "name": "invoice_chat",
            "trigger": "manual",
            "steps": [
                {
                    "action": "send_invoice",
                    "config": {"to": "client@example.com", "amount": 1500},
                }
            ],
        },
    }

    calls = {"count": 0}

    async def _run_idempotent(workflow, *, idempotency_key=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "result": wf_payload,
                "idempotency_key": idempotency_key,
                "idempotent_replay": False,
            }
        return {
            "result": wf_payload,
            "idempotency_key": idempotency_key,
            "idempotent_replay": True,
        }

    with patch("app.routers.chat.run_idempotent_workflow", side_effect=_run_idempotent) as run_idempotent:
        first = await chat._maybe_auto_execute(dict(result), {"text": "uruchom"})
        second = await chat._maybe_auto_execute(dict(result), {"text": "uruchom"})

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert run_idempotent.await_count == 2
    assert run_idempotent.await_args_list[0].kwargs["idempotency_key"] is not None
    assert (
        run_idempotent.await_args_list[0].kwargs["idempotency_key"]
        == run_idempotent.await_args_list[1].kwargs["idempotency_key"]
    )


@pytest.mark.asyncio
async def test_ready_chat_rejects_invalid_dsl_contract_before_execution() -> None:
    result = {
        "status": "ready",
        "auto_execute": True,
        "dsl": {
            "name": "broken_chat",
            "steps": [{"config": {"amount": 1500}}],
        },
    }

    run_workflow = AsyncMock()
    with patch("app.routers.chat.run_idempotent_workflow", run_workflow):
        rejected = await chat._maybe_auto_execute(result, {"text": "uruchom"})

    run_workflow.assert_not_awaited()
    assert rejected["status"] == "validation_failed"
    assert rejected["missing_fields"] == ["steps.0.action"]
    assert rejected["validation_issues"][0]["code"] == "workflow.missing_action"
    assert "Workflow nie został wykonany" in rejected["message"]
