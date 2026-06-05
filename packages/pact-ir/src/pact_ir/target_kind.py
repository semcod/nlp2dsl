"""Execution target and risk enums."""

from __future__ import annotations

from enum import Enum


class TargetKind(str, Enum):
    SHELL = "shell"
    REST = "rest"
    MCP = "mcp"
    WS = "ws"
    BROWSER = "browser"
    DESKTOP = "desktop"
    SQL = "sql"
    UNKNOWN = "unknown"

    @property
    def propact_protocol(self) -> str | None:
        """Map to Propact fenced-block protocol name."""
        mapping = {
            TargetKind.SHELL: "shell",
            TargetKind.REST: "rest",
            TargetKind.MCP: "mcp",
            TargetKind.WS: "ws",
        }
        return mapping.get(self)


class ExecutionRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DESTRUCTIVE = "destructive"
