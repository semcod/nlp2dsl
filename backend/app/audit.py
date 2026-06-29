"""Audit read-model helpers for workflow execution history."""

from __future__ import annotations

from typing import Any


def _extract_actions(steps: list[Any]) -> list[str]:
    return [
        str(step.get("action") or "")
        for step in steps
        if isinstance(step, dict) and step.get("action")
    ]


def _build_entry(run: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    event_types = [str(ev.get("event_type") or ev.get("type") or "") for ev in events]
    return {
        "workflow_id": str(run.get("workflow_id") or ""),
        "name": run.get("name"),
        "status": run.get("status"),
        "trigger": run.get("trigger"),
        "actions": _extract_actions(run.get("steps") or []),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "event_count": len(events),
        "event_types": [t for t in event_types if t],
        "agent_id": run.get("agent_id") or run.get("metadata", {}).get("agent_id"),
    }


def _matches_filters(
    entry: dict[str, Any],
    *,
    agent_id: str | None,
    action: str | None,
) -> bool:
    if action and action not in entry["actions"]:
        return False
    if agent_id and entry.get("agent_id") != agent_id:
        return False
    return True


async def build_audit_entries(
    repo: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    agent_id: str | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    """Aggregate recent workflow runs with event summaries for audit API."""
    runs = await repo.list_runs(limit=limit, offset=offset)
    entries: list[dict[str, Any]] = []

    for run in runs:
        workflow_id = str(run.get("workflow_id") or "")
        events = await repo.list_events(workflow_id, limit=20, offset=0)
        entry = _build_entry(run, events)
        if _matches_filters(entry, agent_id=agent_id, action=action):
            entries.append(entry)

    total = await repo.count_runs()
    return {
        "entries": entries,
        "count": len(entries),
        "total_runs": total,
        "limit": limit,
        "offset": offset,
    }
