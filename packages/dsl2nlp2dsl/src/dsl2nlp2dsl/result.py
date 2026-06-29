"""DslResult — shared result type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DslResult:
    ok: bool
    command: str
    action: str = ""
    output: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "command": self.command,
            "action": self.action,
            "output": self.output,
            "data": self.data,
            "error": self.error,
            "event_id": self.event_id,
        }
