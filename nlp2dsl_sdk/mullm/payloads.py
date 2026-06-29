"""Map nlp2dsl Mullm action steps to Mullm CreateTaskCommand payloads."""

from __future__ import annotations

from typing import Any, Callable

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

_ActionFields = tuple[str, str, str]  # title, description, shell_command


def is_mullm_action(action: str) -> bool:
    return str(action or "").startswith("mullm_") or action in MULLM_ACTIONS


def _cfg(step: dict[str, Any]) -> dict[str, Any]:
    raw = step.get("config") or step.get("parameters") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _shell_task_fields(cfg: dict[str, Any], *, title: str, description: str, shell_command: str) -> _ActionFields:
    shell = shell_command or str(cfg.get("script") or "")
    desc = str(cfg.get("description") or f"Shell task: {shell[:120]}")
    return title, desc, shell


def _browser_task_fields(cfg: dict[str, Any], *, title: str, description: str, shell_command: str) -> _ActionFields:
    url = str(cfg.get("url") or "")
    instructions = str(cfg.get("instructions") or cfg.get("goal") or description)
    desc = f"Browser task\nURL: {url}\n{instructions}".strip()
    return title, desc, shell_command


def _db_query_fields(cfg: dict[str, Any], *, title: str, description: str, shell_command: str) -> _ActionFields:
    query = str(cfg.get("query") or cfg.get("sql") or "")
    engine = str(cfg.get("engine") or cfg.get("dialect") or "sql")
    desc = f"DB query ({engine}): {query or description}"
    shell = shell_command or query
    return title, desc, shell


def _select_agent_fields(cfg: dict[str, Any], *, title: str, description: str, shell_command: str) -> _ActionFields:
    role = str(cfg.get("preferred_role") or cfg.get("role") or "")
    desc = str(
        cfg.get("description")
        or f"Select agent role={role} source={cfg.get('source', 'nlp2dsl')}"
    )
    return title, desc, shell_command


def _delegate_fields(cfg: dict[str, Any], *, title: str, description: str, shell_command: str) -> _ActionFields:
    desc = str(cfg.get("description") or cfg.get("objective") or title)
    return title, desc, shell_command


_ACTION_FIELD_BUILDERS: dict[str, Callable[..., _ActionFields]] = {
    "mullm_shell_task": _shell_task_fields,
    "mullm_browser_task": _browser_task_fields,
    "mullm_db_query": _db_query_fields,
    "mullm_select_agent": _select_agent_fields,
    "mullm_delegate": _delegate_fields,
}


def _resolve_action_fields(
    action: str,
    cfg: dict[str, Any],
    *,
    title: str,
    description: str,
    shell_command: str,
) -> _ActionFields:
    builder = _ACTION_FIELD_BUILDERS.get(action)
    if builder is None:
        return title, description, shell_command
    return builder(cfg, title=title, description=description, shell_command=shell_command)


def _parse_auto_assign(cfg: dict[str, Any]) -> bool:
    auto_assign = cfg.get("auto_assign", True)
    if isinstance(auto_assign, str):
        return auto_assign.lower() not in {"false", "0", "no"}
    return bool(auto_assign)


def _build_payload_core(
    action: str,
    cfg: dict[str, Any],
    step_id: str,
) -> dict[str, Any]:
    title = str(cfg.get("title") or cfg.get("name") or f"{action}:{step_id}")
    description = str(cfg.get("description") or cfg.get("prompt") or title)
    shell_command = str(cfg.get("shell_command") or cfg.get("command") or "").strip()

    title, description, shell_command = _resolve_action_fields(
        action,
        cfg,
        title=title,
        description=description,
        shell_command=shell_command,
    )

    return {
        "title": title[:500],
        "description": description[:4000],
        "shell_command": shell_command[:8000],
        "source": str(cfg.get("source") or "nlp2dsl"),
        "auto_assign": _parse_auto_assign(cfg),
    }


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

    payload = _build_payload_core(action, cfg, step_id)

    preferred_role = cfg.get("preferred_role") or cfg.get("role")
    if preferred_role:
        payload["preferred_role"] = str(preferred_role)
    if workflow_id:
        payload["source_command_id"] = f"{workflow_id}:{step_id}"
    if session_id:
        payload["session_id"] = session_id
    return payload
