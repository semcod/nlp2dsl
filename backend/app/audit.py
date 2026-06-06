"""Audit read-model helpers for workflow execution history."""

from __future__ import annotations

from typing import Any


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
        steps = run.get("steps") or []
        actions = [
            str(step.get("action") or "")
            for step in steps
            if isinstance(step, dict) and step.get("action")
        ]
        if action and action not in actions:
            continue

        events = await repo.list_events(workflow_id, limit=20, offset=0)
        event_types = [str(ev.get("event_type") or ev.get("type") or "") for ev in events]

        entry = {
            "workflow_id": workflow_id,
            "name": run.get("name"),
            "status": run.get("status"),
            "trigger": run.get("trigger"),
            "actions": actions,
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "event_count": len(events),
            "event_types": [t for t in event_types if t],
            "agent_id": run.get("agent_id") or run.get("metadata", {}).get("agent_id"),
        }
        if agent_id and entry.get("agent_id") != agent_id:
            continue
        entries.append(entry)

    total = await repo.count_runs()
    return {
        "entries": entries,
        "count": len(entries),
        "total_runs": total,
        "limit": limit,
        "offset": offset,
    }
