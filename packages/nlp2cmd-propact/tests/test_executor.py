from __future__ import annotations

from unittest.mock import MagicMock, patch

from pact_ir import ExecutionPlanIR, PlanStep, TargetKind

from nlp2cmd_propact.executor import HybridPlanExecutor, execution_route


def _shell_plan() -> ExecutionPlanIR:
    return ExecutionPlanIR(
        query="find py",
        source="rule_shell",
        steps=[
            PlanStep(
                id="s1",
                action="shell_find",
                target_kind=TargetKind.SHELL,
                dsl='find src -name "*.py"',
            )
        ],
    )


def _browser_plan() -> ExecutionPlanIR:
    return ExecutionPlanIR(
        query="open site",
        source="browser",
        steps=[
            PlanStep(
                id="s1",
                action="navigate",
                target_kind=TargetKind.BROWSER,
                dsl='{"format":"dom_dql.v1","url":"https://example.com"}',
            )
        ],
    )


def test_execution_route():
    assert execution_route(PlanStep(id="s1", action="x", target_kind=TargetKind.SHELL)) == "propact"
    assert execution_route(PlanStep(id="s1", action="x", target_kind=TargetKind.REST)) == "propact"
    assert execution_route(PlanStep(id="s1", action="x", target_kind=TargetKind.BROWSER)) == "nlp2cmd"


def test_hybrid_dry_run_includes_routes():
    result = HybridPlanExecutor().run(_shell_plan(), dry_run=True)
    assert result.success is True
    assert result.metadata["routes"][0]["route"] == "propact"


@patch.object(HybridPlanExecutor, "_run_propact_step")
def test_hybrid_routes_shell_to_propact(mock_propact):
    mock_propact.return_value = MagicMock(success=True, stdout="files", stderr="", metadata={})
    result = HybridPlanExecutor().run(_shell_plan(), dry_run=False)
    assert result.success is True
    mock_propact.assert_called_once()


@patch.object(HybridPlanExecutor, "_run_nlp2cmd_step")
def test_hybrid_routes_browser_to_nlp2cmd(mock_nlp2cmd):
    mock_nlp2cmd.return_value = MagicMock(success=True, stdout="", stderr="", metadata={})
    result = HybridPlanExecutor().run(_browser_plan(), dry_run=False)
    assert result.success is True
    mock_nlp2cmd.assert_called_once()


@patch.object(HybridPlanExecutor, "_run_propact_step")
def test_hybrid_stops_on_first_failure(mock_propact):
    mock_propact.return_value = MagicMock(
        success=False,
        stdout="",
        stderr="boom",
        metadata={"executor": "propact"},
    )
    result = HybridPlanExecutor().run(_shell_plan(), dry_run=False)
    assert result.success is False
    assert "boom" in result.stderr
