from __future__ import annotations

from unittest.mock import patch

import pytest
from pact_ir import ExecutionPlanIR, PlanStep, TargetKind

from nlp2cmd_propact.runner import PropactRunner, RunResult, _run_shell_steps


def _shell_plan(dsl: str = 'find src -name "*.py"') -> ExecutionPlanIR:
    return ExecutionPlanIR(
        query="find py",
        source="rule_shell",
        steps=[
            PlanStep(
                id="s1",
                action="shell_find",
                target_kind=TargetKind.SHELL,
                dsl=dsl,
            )
        ],
    )


def test_run_dry_run_returns_markdown_only():
    runner = PropactRunner()
    result = runner.run(_shell_plan(), dry_run=True)
    assert result.success is True
    assert result.metadata.get("dry_run") is True
    assert "```propact:shell" in result.markdown
    assert result.stdout == ""


@patch("nlp2cmd_propact.runner.subprocess.run")
@patch("nlp2cmd_propact.runner._propact_available", return_value=True)
def test_run_executes_propact_without_dry_run(mock_available, mock_run):
    mock_run.return_value = type("P", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    runner = PropactRunner(propact_bin="propact")
    result = runner.run(_shell_plan(), dry_run=False)

    assert result.success is True
    assert result.metadata["executor"] == "propact"
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "propact"
    assert cmd[1] == "run"
    assert "--dry-run" not in cmd


@patch("nlp2cmd_propact.runner.subprocess.run")
@patch("nlp2cmd_propact.runner._propact_available", return_value=False)
def test_shell_fallback_when_propact_missing(mock_available, mock_run):
    mock_run.return_value = type(
        "P",
        (),
        {"returncode": 0, "stdout": "./a.py\n", "stderr": ""},
    )()

    runner = PropactRunner()
    result = runner.run(_shell_plan(), dry_run=False)

    assert result.success is True
    assert result.metadata["executor"] == "shell_fallback"
    assert "./a.py" in result.stdout
    executed = mock_run.call_args[0][0]
    assert executed == ["find", "src", "-name", "*.py"]


@patch("nlp2cmd_propact.runner._propact_available", return_value=False)
def test_rest_plan_fails_without_propact(mock_available):
    plan = ExecutionPlanIR(
        query="call api",
        source="rest",
        steps=[
            PlanStep(
                id="s1",
                action="http_get",
                target_kind=TargetKind.REST,
                params={"method": "GET", "endpoint": "/health"},
            )
        ],
    )
    result = PropactRunner().run(plan, dry_run=False)
    assert result.success is False
    assert "propact CLI not found" in result.stderr
    assert "rest/mcp/ws" in result.stderr


@patch("nlp2cmd_propact.runner._propact_available", return_value=False)
def test_shell_fallback_disabled_returns_error(mock_available, monkeypatch):
    monkeypatch.setenv("NLP2CMD_PROPACT_FALLBACK", "error")
    result = PropactRunner().run(_shell_plan(), dry_run=False)
    assert result.success is False
    assert "NLP2CMD_PROPACT_FALLBACK=shell" in result.stderr


def test_shell_fallback_propagates_nonzero_exit():
    plan = _shell_plan(dsl="false")
    with patch("nlp2cmd_propact.runner.subprocess.run") as mock_run:
        mock_run.return_value = type(
            "P",
            (),
            {"returncode": 1, "stdout": "", "stderr": "failed"},
        )()
        result = _run_shell_steps(plan)
    assert result.success is False
    assert result.metadata["returncode"] == 1


def test_empty_plan_fails():
    plan = ExecutionPlanIR(query="empty", source="test", steps=[])
    result = PropactRunner().run(plan, dry_run=False)
    assert result.success is False
    assert "no steps" in result.stderr


@patch("nlp2cmd_propact.runner.subprocess.run")
@patch("nlp2cmd_propact.runner._propact_available", return_value=True)
def test_propact_bin_env_override(mock_available, mock_run, monkeypatch):
    monkeypatch.setenv("NLP2CMD_PROPACT_BIN", "/custom/propact")
    mock_run.return_value = type("P", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    PropactRunner().run(_shell_plan(), dry_run=False)
    assert mock_run.call_args[0][0][0] == "/custom/propact"
