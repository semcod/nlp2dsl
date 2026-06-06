"""Post-execute validation — worker outcome + attachment artifacts."""

from __future__ import annotations

from typing import Any

from ..context import ValidationContext
from ..issue import Phase, ValidationIssue
from .step_config import validate_step


def _invalid_steps_payload() -> list[ValidationIssue]:
    return [
        ValidationIssue(
            code="execution.invalid_payload",
            field_name="steps",
            message="execution.steps must be a list",
            phase=Phase.POST_EXECUTE,
            kind="invalid_format",
            resolution="blocked",
        )
    ]


def _failed_step_issues(steps: list[Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        if str(step.get("status") or "") != "failed":
            continue
        action = str(step.get("action") or "")
        err = step.get("error") or step.get("detail") or "unknown error"
        issues.append(
            ValidationIssue(
                code="execution.step_failed",
                field_name="status",
                message=f"krok {index + 1} ({action or '?'}): {err}",
                phase=Phase.POST_EXECUTE,
                kind="blocked",
                resolution="blocked",
                meta={"step_index": index, "action": action},
            )
        )
    return issues


def _dsl_attachment_issues(
    dsl: dict[str, Any],
    *,
    path_resolver,
    path_scope_check=None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for step in dsl.get("steps") or []:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "")
        config = dict(step.get("config") or {})
        if not str(config.get("attachment_path") or "").strip():
            continue
        ctx = ValidationContext(
            phase=Phase.POST_EXECUTE,
            action=action,
            config=config,
            path_resolver=path_resolver,
            path_scope_check=path_scope_check,
        )
        issues.extend(validate_step(ctx))
    return issues


def validate_execution_outcome(
    execution: dict[str, Any],
    *,
    dsl: dict[str, Any] | None = None,
    path_resolver=None,
    path_scope_check=None,
) -> list[ValidationIssue]:
    """Validate completed workflow execution (step status + optional attachment re-check)."""
    steps = execution.get("steps") or []
    if not isinstance(steps, list):
        return _invalid_steps_payload()

    issues = _failed_step_issues(steps)
    if dsl and path_resolver is not None:
        issues.extend(
            _dsl_attachment_issues(dsl, path_resolver=path_resolver, path_scope_check=path_scope_check)
        )
    return issues
