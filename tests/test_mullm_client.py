"""Tests for Mullm delegate client and workflow executor."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from nlp2dsl_sdk.mullm.client import MullmClient, MullmClientError
from nlp2dsl_sdk.mullm.executor import execute_mullm_workflow
from nlp2dsl_sdk.mullm.payloads import build_task_payload


def test_build_task_payload_shell_task() -> None:
    payload = build_task_payload(
        {
            "id": "s1",
            "action": "mullm_shell_task",
            "config": {"shell_command": "ls -la", "title": "List files"},
        },
        workflow_id="wf-1",
    )
    assert payload["shell_command"] == "ls -la"
    assert payload["title"] == "List files"
    assert payload["source"] == "nlp2dsl"
    assert payload["auto_assign"] is True
    assert payload["source_command_id"] == "wf-1:s1"


def test_execute_mullm_workflow_simulate_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULLM_DELEGATE_MODE", "simulate")
    workflow = {
        "id": "wf-mullm",
        "name": "shell_job",
        "steps": [
            {
                "id": "run",
                "action": "mullm_shell_task",
                "config": {"shell_command": "echo hello"},
            }
        ],
    }
    result = execute_mullm_workflow(workflow)
    assert result["status"] == "completed"
    assert result["execution_backend"] == "mullm"
    assert result["simulated"] is True
    step = result["steps"][0]
    assert step["status"] == "completed"
    assert step["result"]["transport"] == "simulated"
    assert step["result"]["task_id"].startswith("SIM-TASK-")


def test_mullm_client_create_task_success() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"task_id": "T-42", "command_id": "C-99", "status": "queued"}
    session.post.return_value = response

    client = MullmClient(base_url="http://mullm.test", session=session)
    out = client.create_task({"title": "t", "description": "d", "shell_command": "true"})

    assert out["task_id"] == "T-42"
    session.post.assert_called_once()
    assert session.post.call_args.args[0] == "http://mullm.test/api/commands/tasks"


def test_mullm_client_create_task_http_error() -> None:
    session = MagicMock()
    response = MagicMock()
    response.status_code = 422
    response.json.return_value = {"detail": "invalid"}
    session.post.return_value = response

    client = MullmClient(base_url="http://mullm.test", session=session)
    with pytest.raises(MullmClientError) as exc:
        client.create_task({"title": "t"})
    assert exc.value.status_code == 422


def test_execute_mullm_workflow_live_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULLM_DELEGATE_MODE", "live")
    workflow = {
        "steps": [{"action": "mullm_delegate", "config": {"title": "Job", "description": "Do it"}}],
    }

    with patch.object(MullmClient, "ping", return_value=True):
        with patch.object(
            MullmClient,
            "create_task",
            return_value={"task_id": "LIVE-1", "command_id": "CMD-1"},
        ) as create_task:
            result = execute_mullm_workflow(workflow)

    create_task.assert_called_once()
    assert result["status"] == "completed"
    assert result["simulated"] is False
    assert result["steps"][0]["result"]["transport"] == "mullm_api"
    assert result["steps"][0]["result"]["task_id"] == "LIVE-1"


def test_execute_mullm_workflow_rejects_mixed_steps() -> None:
    workflow = {
        "steps": [
            {"action": "mullm_shell_task", "config": {}},
            {"action": "send_email", "config": {"to": "a@b.c"}},
        ],
    }
    with pytest.raises(ValueError, match="mixes Mullm"):
        execute_mullm_workflow(workflow)
