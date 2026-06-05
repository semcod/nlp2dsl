"""Hybrid execution: Propact for shell/rest/mcp/ws, nlp2cmd for other targets."""

from __future__ import annotations

from typing import Any

from pact_ir import ExecutionPlanIR, PlanStep, TargetKind

from nlp2cmd_propact.adapter import step_to_propact_block
from nlp2cmd_propact.runner import PropactRunner, RunResult

_PROPACT_KINDS = frozenset(
    {
        TargetKind.SHELL,
        TargetKind.REST,
        TargetKind.MCP,
        TargetKind.WS,
    }
)
_NLP2CMD_KINDS = frozenset(
    {
        TargetKind.BROWSER,
        TargetKind.DESKTOP,
        TargetKind.SQL,
        TargetKind.UNKNOWN,
    }
)


def execution_route(step: PlanStep) -> str:
    """Return executor name for a plan step."""
    if step.target_kind in _PROPACT_KINDS:
        return "propact"
    if step.target_kind in _NLP2CMD_KINDS:
        return "nlp2cmd"
    return "nlp2cmd"


def _single_step_plan(plan: ExecutionPlanIR, step: PlanStep) -> ExecutionPlanIR:
    return ExecutionPlanIR(
        query=plan.query,
        source=plan.source,
        confidence=plan.confidence,
        steps=[step],
        metadata=dict(plan.metadata),
    )


class HybridPlanExecutor:
    """Route plan steps to Propact or nlp2cmd based on target_kind."""

    def __init__(self, *, propact_runner: PropactRunner | None = None):
        self.propact_runner = propact_runner or PropactRunner()

    def run(self, plan: ExecutionPlanIR, *, dry_run: bool = False) -> RunResult:
        if dry_run:
            return RunResult(
                success=True,
                markdown=self.propact_runner.render(plan),
                metadata={
                    "dry_run": True,
                    "routes": [
                        {"step": step.id, "route": execution_route(step)}
                        for step in plan.steps
                    ],
                },
            )

        if not plan.steps:
            return RunResult(
                success=False,
                markdown=self.propact_runner.render(plan),
                stderr="execution plan has no steps",
            )

        markdown = self.propact_runner.render(plan)
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        step_results: list[dict[str, Any]] = []

        for step in plan.steps:
            route = execution_route(step)
            if route == "propact":
                step_result = self._run_propact_step(plan, step)
            else:
                step_result = self._run_nlp2cmd_step(plan, step, dry_run=dry_run)

            step_results.append(
                {
                    "step": step.id,
                    "action": step.action,
                    "route": route,
                    "success": step_result.success,
                    "stdout": step_result.stdout,
                    "stderr": step_result.stderr,
                    "metadata": {
                        **step_result.metadata,
                        "returncode": 0 if step_result.success else 1,
                    },
                }
            )
            if step_result.stdout:
                stdout_parts.append(step_result.stdout.rstrip("\n"))
            if step_result.stderr:
                stderr_parts.append(step_result.stderr.rstrip("\n"))
            if not step_result.success:
                return RunResult(
                    success=False,
                    markdown=markdown,
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                    metadata={"executor": "hybrid", "steps": step_results},
                )

        return RunResult(
            success=True,
            markdown=markdown,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
            metadata={"executor": "hybrid", "steps": step_results},
        )

    def _run_propact_step(self, plan: ExecutionPlanIR, step: PlanStep) -> RunResult:
        mini_plan = _single_step_plan(plan, step)
        return self.propact_runner.run(mini_plan, dry_run=False)

    def _run_nlp2cmd_step(
        self,
        plan: ExecutionPlanIR,
        step: PlanStep,
        *,
        dry_run: bool,
    ) -> RunResult:
        try:
            from nlp2cmd.bridge.plan_execute import run_plan_step
        except ImportError:
            block = step_to_propact_block(step)
            return RunResult(
                success=False,
                markdown=block,
                stderr=(
                    f"nlp2cmd not available for target_kind={step.target_kind.value}; "
                    "install nlp2cmd and retry"
                ),
                metadata={"executor": "nlp2cmd", "missing": True},
            )

        payload = run_plan_step(step, plan, dry_run=dry_run)
        return RunResult(
            success=bool(payload.get("success")),
            markdown=step_to_propact_block(step),
            stdout=str(payload.get("stdout") or ""),
            stderr=str(payload.get("stderr") or ""),
            metadata=dict(payload.get("metadata") or {}),
        )
