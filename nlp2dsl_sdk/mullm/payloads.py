"""Map nlp2dsl Mullm action steps to Mullm CreateTaskCommand payloads."""

from __future__ import annotations

from typing import Any

MULLM_ACTIONS = frozenset(
    {
        "mullm_shell_task",
        "mullm_browser_task",
        "mullm_db_query",
        "mullm_delegate",
        "mullm_create_task",
        "mullm_select_agent",
    }
)


def is_mullm_action(action: str) -> bool:
    return str(action or "").startswith("mullm_") or action in MULLM_ACTIONS


def _cfg(step: dict[str, Any]) -> dict[str, Any]:
    raw = step.get("config") or step.get("parameters") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def build_task_payload(
    step: dict[str, Any],
    *,
    workflow_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Build POST /api/commands/tasks body for one workflow step."""
    action = str(step.get("action") or "")
    cfg = _cfg(step)
    step_id = str(step.get("id") or step.get("step_id") or "step")
    title = str(cfg.get("title") or cfg.get("name") or f"{action}:{step_id}")
    description = str(cfg.get("description") or cfg.get("prompt") or title)
    shell_command = str(cfg.get("shell_command") or cfg.get("command") or "").strip()

    if action == "mullm_shell_task":
        shell_command = shell_command or str(cfg.get("script") or "")
        description = str(cfg.get("description") or f"Shell task: {shell_command[:120]}")
    elif action == "mullm_browser_task":
        url = str(cfg.get("url") or "")
        instructions = str(cfg.get("instructions") or cfg.get("goal") or description)
        description = f"Browser task\nURL: {url}\n{instructions}".strip()
    elif action == "mullm_db_query":
        query = str(cfg.get("query") or cfg.get("sql") or "")
        engine = str(cfg.get("engine") or cfg.get("dialect") or "sql")
        description = f"DB query ({engine}): {query or description}"
        if not shell_command and query:
            shell_command = query
    elif action == "mullm_select_agent":
        role = str(cfg.get("preferred_role") or cfg.get("role") or "")
        description = str(
            cfg.get("description")
            or f"Select agent role={role} source={cfg.get('source', 'nlp2dsl')}"
        )
    elif action == "mullm_delegate":
        description = str(cfg.get("description") or cfg.get("objective") or title)

    preferred_role = cfg.get("preferred_role") or cfg.get("role")
    auto_assign = cfg.get("auto_assign", True)
    if isinstance(auto_assign, str):
        auto_assign = auto_assign.lower() not in {"false", "0", "no"}

    payload: dict[str, Any] = {
        "title": title[:500],
        "description": description[:4000],
        "shell_command": shell_command[:8000],
        "source": str(cfg.get("source") or "nlp2dsl"),
        "auto_assign": bool(auto_assign),
    }
    if preferred_role:
        payload["preferred_role"] = str(preferred_role)
    if workflow_id:
        payload["source_command_id"] = f"{workflow_id}:{step_id}"
    if session_id:
        payload["session_id"] = session_id
    return payload
