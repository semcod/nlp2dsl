"""Stdio MCP server — safe workflow plan/validate/execute for agents."""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore


def _client():
    from nlp2dsl_sdk.client import NLP2DSLClient

    return NLP2DSLClient.from_env()


def _plan_workflow(text: str, mode: str = "auto") -> dict[str, Any]:
    import httpx

    backend = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
    resp = httpx.post(
        f"{backend}/workflow/plan",
        json={"text": text, "mode": mode},
        timeout=float(os.getenv("NLP2DSL_TIMEOUT", "30")),
    )
    resp.raise_for_status()
    return resp.json()


def _validate_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    import httpx

    backend = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
    resp = httpx.post(
        f"{backend}/workflow/validate",
        json={"workflow": workflow},
        timeout=float(os.getenv("NLP2DSL_TIMEOUT", "30")),
    )
    resp.raise_for_status()
    return resp.json()


def _execute_workflow(workflow: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    import httpx

    backend = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
    resp = httpx.post(
        f"{backend}/workflow/execute",
        json={"workflow": workflow, "dry_run": dry_run},
        timeout=float(os.getenv("NLP2DSL_TIMEOUT", "60")),
    )
    resp.raise_for_status()
    return resp.json()


def build_mcp() -> Any:
    if FastMCP is None:
        raise RuntimeError("mcp package required: pip install nlp2dsl-mcp")

    mcp = FastMCP("nlp2dsl")

    @mcp.tool()
    def nlp2dsl_plan(text: str, mode: str = "auto") -> str:
        """Plan a workflow from natural language without executing side effects."""
        return json.dumps(_plan_workflow(text, mode=mode), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_validate(workflow_json: str) -> str:
        """Validate a workflow DSL JSON before execution."""
        workflow = json.loads(workflow_json)
        return json.dumps(_validate_workflow(workflow), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_execute(workflow_json: str, dry_run: bool = False) -> str:
        """Execute a validated workflow (use dry_run=true to preview dispatch only)."""
        workflow = json.loads(workflow_json)
        return json.dumps(_execute_workflow(workflow, dry_run=dry_run), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_health() -> str:
        """Check NLP2DSL backend, nlp-service and worker health."""
        with _client() as client:
            return json.dumps(client.health(), ensure_ascii=False, indent=2)

    return mcp


def main() -> None:
    mcp = build_mcp()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
