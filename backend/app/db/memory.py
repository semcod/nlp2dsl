"""
MemoryWorkflowRepo — in-memory fallback (zachowanie dotychczasowe).
"""

from collections import OrderedDict

from app.db import DEFAULT_LIST_LIMIT, WorkflowRepo


DEFAULT_MAX_SIZE: int = int("10000")


class MemoryWorkflowRepo(WorkflowRepo):

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE):
        self._data: OrderedDict[str, dict] = OrderedDict()
        self._events: dict[str, list[dict]] = {}
        self._max_size = max_size

    async def save_run(self, workflow_id: str, name: str, status: str, data: dict) -> None:
        while len(self._data) >= self._max_size:
            self._data.popitem(last=False)
        self._data[workflow_id] = {"workflow_id": workflow_id, "name": name, "status": status, **data}
        self._data.move_to_end(workflow_id)

    async def update_run_status(self, workflow_id: str, status: str) -> None:
        if workflow_id in self._data:
            self._data[workflow_id]["status"] = status

    async def get_run(self, workflow_id: str) -> dict | None:
        return self._data.get(workflow_id)

    async def list_runs(self, limit: int = DEFAULT_LIST_LIMIT, offset: int = 0) -> list[dict]:
        items = list(reversed(self._data.values()))
        return items[offset:offset + limit]

    async def count_runs(self) -> int:
        return len(self._data)

    async def append_event(self, workflow_id: str, event: dict) -> None:
        self._events.setdefault(workflow_id, []).append(dict(event))

    async def list_events(
        self,
        workflow_id: str,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[dict]:
        events = self._events.get(workflow_id, [])
        return events[offset : offset + limit]
