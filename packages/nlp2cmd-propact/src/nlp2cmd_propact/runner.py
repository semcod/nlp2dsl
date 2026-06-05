"""Execute plans via Propact or subprocess fallback."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pact_ir import ExecutionPlanIR, TargetKind

from nlp2cmd_propact.adapter import plan_to_propact_markdown

_PROPACT_BIN_ENV = "NLP2CMD_PROPACT_BIN"
_FALLBACK_ENV = "NLP2CMD_PROPACT_FALLBACK"
_PROPACT_PROTOCOLS = frozenset({TargetKind.SHELL, TargetKind.REST, TargetKind.MCP, TargetKind.WS})


@dataclass
class RunResult:
    success: bool
    markdown: str
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _propact_fallback_mode() -> str:
    return os.getenv(_FALLBACK_ENV, "shell").strip().lower()


def _resolve_propact_bin(propact_bin: str) -> str:
    return os.getenv(_PROPACT_BIN_ENV, propact_bin).strip() or propact_bin


def _propact_available(propact_bin: str) -> bool:
    resolved = _resolve_propact_bin(propact_bin)
    return shutil.which(resolved) is not None


def _is_shell_only(plan: ExecutionPlanIR) -> bool:
    return bool(plan.steps) and all(step.target_kind == TargetKind.SHELL for step in plan.steps)


def _requires_propact(plan: ExecutionPlanIR) -> bool:
    return any(step.target_kind in _PROPACT_PROTOCOLS - {TargetKind.SHELL} for step in plan.steps)


def _shell_command(step_dsl: str, step_params: dict[str, Any]) -> str:
    command = (step_dsl or step_params.get("command", "")).strip()
    if not command:
        raise ValueError("shell step has empty dsl/command")
    return command


def _run_shell_steps(plan: ExecutionPlanIR) -> RunResult:
    markdown = plan_to_propact_markdown(plan)
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []

    for step in plan.steps:
        try:
            command = _shell_command(step.dsl, step.params)
        except ValueError as exc:
            return RunResult(
                success=False,
                markdown=markdown,
                stderr=str(exc),
                metadata={"executor": "shell_fallback", "failed_step": step.id},
            )

        try:
            proc = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, ValueError) as exc:
            return RunResult(
                success=False,
                markdown=markdown,
                stderr=str(exc),
                metadata={"executor": "shell_fallback", "failed_step": step.id},
            )

        if proc.stdout:
            stdout_parts.append(proc.stdout.rstrip("\n"))
        if proc.stderr:
            stderr_parts.append(proc.stderr.rstrip("\n"))
        if proc.returncode != 0:
            return RunResult(
                success=False,
                markdown=markdown,
                stdout="\n".join(stdout_parts),
                stderr="\n".join(stderr_parts),
                metadata={
                    "executor": "shell_fallback",
                    "failed_step": step.id,
                    "returncode": proc.returncode,
                },
            )

    return RunResult(
        success=True,
        markdown=markdown,
        stdout="\n".join(stdout_parts),
        stderr="\n".join(stderr_parts),
        metadata={"executor": "shell_fallback", "steps": len(plan.steps)},
    )


class PropactRunner:
    """Run ExecutionPlanIR through Propact CLI when available."""

    def __init__(self, *, propact_bin: str = "propact"):
        self.propact_bin = propact_bin

    def render(self, plan: ExecutionPlanIR) -> str:
        return plan_to_propact_markdown(plan)

    def run(self, plan: ExecutionPlanIR, *, dry_run: bool = False) -> RunResult:
        markdown = self.render(plan)
        if dry_run:
            return RunResult(success=True, markdown=markdown, metadata={"dry_run": True})

        if not plan.steps:
            return RunResult(
                success=False,
                markdown=markdown,
                stderr="execution plan has no steps",
            )

        propact_bin = _resolve_propact_bin(self.propact_bin)
        if _propact_available(self.propact_bin):
            return self._run_via_propact(markdown, propact_bin)

        if _requires_propact(plan):
            return RunResult(
                success=False,
                markdown=markdown,
                stderr=(
                    "propact CLI not found; plan requires rest/mcp/ws execution. "
                    "Install: pip install 'propact[semantic]'"
                ),
                metadata={"executor": "propact", "missing": True},
            )

        if _is_shell_only(plan) and _propact_fallback_mode() == "shell":
            return _run_shell_steps(plan)

        if _propact_fallback_mode() == "error":
            return RunResult(
                success=False,
                markdown=markdown,
                stderr="propact CLI not found; set NLP2CMD_PROPACT_FALLBACK=shell for shell-only plans",
                metadata={"executor": "propact", "missing": True},
            )

        return RunResult(
            success=False,
            markdown=markdown,
            stderr="no executor available for this plan",
        )

    def _run_via_propact(self, markdown: str, propact_bin: str) -> RunResult:
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "plan.md"
            md_path.write_text(markdown, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [propact_bin, "run", str(md_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                return RunResult(
                    success=False,
                    markdown=markdown,
                    stderr="propact CLI not found; pip install propact",
                    metadata={"executor": "propact", "missing": True},
                )
            return RunResult(
                success=proc.returncode == 0,
                markdown=markdown,
                stdout=proc.stdout,
                stderr=proc.stderr,
                metadata={"executor": "propact", "returncode": proc.returncode},
            )
