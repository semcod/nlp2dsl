"""Structured attachment_path validation (process.paths + file + invoice PDF)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from app.conversation.doql_context import resolve_doql_context_path
from app.conversation.system_map import get_doql_context
from app.validation.path_policy import validate_process_path
from app.validation.path_resolve import resolve_attachment_path
from app.validation.step_validator import validate_step_config

AttachmentStatus = Literal["ok", "missing", "invalid", "denied", "skipped"]


def _check_process_scope(
    resolved: str,
    *,
    access: str,
) -> tuple[AttachmentStatus, list[str]]:
    ctx = get_doql_context()
    if ctx is None:
        return "ok", []
    scope_msg = validate_process_path(ctx, resolved, access=access)
    if scope_msg:
        return "denied", [scope_msg]
    return "ok", []


def _check_step_issues(
    raw: str,
    action: str,
    config: dict[str, Any] | None,
) -> list[str]:
    cfg = dict(config or {})
    cfg.setdefault("attachment_path", raw)
    step_issues = validate_step_config(action, cfg)
    return [i for i in step_issues if "attachment_path" in i]


def _check_path_exists(
    raw: str,
    resolved: str,
    current_status: AttachmentStatus,
    step_issues: list[str],
) -> tuple[AttachmentStatus, list[str]]:
    issues = list(step_issues)
    path = Path(resolved)
    if not path.is_file():
        if current_status != "denied":
            current_status = "missing"
        if not any("nie istnieje" in i for i in issues):
            issues.append(f"attachment_path: plik nie istnieje: {raw}")
    elif step_issues and current_status == "ok":
        current_status = "invalid"
    return current_status, issues


def build_attachment_validation(
    raw_path: str,
    *,
    action: str = "send_invoice",
    config: dict[str, Any] | None = None,
    access: str = "read",
) -> dict[str, Any]:
    """
    Validate attachment_path for workflow steps.

    Returns dict: path, resolved, status, issues[] — attached to chat/execution artifacts.
    """
    raw = (raw_path or "").strip()
    if not raw:
        return {
            "path": "",
            "resolved": "",
            "status": "skipped",
            "issues": [],
        }

    doql = resolve_doql_context_path()
    resolved = resolve_attachment_path(raw, doql_path=doql)

    status, issues = _check_process_scope(resolved, access=access)
    step_issues = _check_step_issues(raw, action, config)
    issues = [i for i in step_issues if i not in issues] + issues

    status, issues = _check_path_exists(raw, resolved, status, issues)

    return {
        "path": raw,
        "resolved": resolved,
        "status": status,
        "issues": issues,
    }
