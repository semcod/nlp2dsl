"""Stdio MCP server — delegates to mcp2nlp2dsl / dsl2nlp2dsl."""

from __future__ import annotations

import json
import warnings
from typing import Any


def build_mcp() -> Any:
    """Build MCP app — prefers mcp2nlp2dsl, falls back to legacy HTTP tools."""
    try:
        from mcp2nlp2dsl.server import build_mcp as _build_control_mcp

        mcp = _build_control_mcp("nlp2dsl")
        _register_legacy_tools(mcp)
        return mcp
    except ImportError:
        warnings.warn("mcp2nlp2dsl not installed — using legacy HTTP-only MCP", stacklevel=2)
        return _build_legacy_mcp()


def _register_legacy_tools(mcp: Any) -> None:
    """Keep backward-compatible workflow HTTP tools alongside DSL control layer."""

    @mcp.tool()
    def nlp2dsl_plan(text: str, mode: str = "auto") -> str:
        """[legacy] Plan workflow via backend HTTP."""
        return json.dumps(_plan_workflow(text, mode=mode), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_validate(workflow_json: str) -> str:
        """[legacy] Validate workflow JSON via backend HTTP."""
        workflow = json.loads(workflow_json)
        return json.dumps(_validate_workflow(workflow), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_execute(workflow_json: str, dry_run: bool = False) -> str:
        """[legacy] Execute workflow via backend HTTP."""
        workflow = json.loads(workflow_json)
        return json.dumps(_execute_workflow(workflow, dry_run=dry_run), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_health() -> str:
        """Check NLP2DSL backend, nlp-service and worker health."""
        with _client() as client:
            return json.dumps(client.health(), ensure_ascii=False, indent=2)


def _build_legacy_mcp() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("mcp package required: pip install nlp2dsl-mcp") from exc

    mcp = FastMCP("nlp2dsl")

    @mcp.tool()
    def nlp2dsl_plan(text: str, mode: str = "auto") -> str:
        return json.dumps(_plan_workflow(text, mode=mode), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_validate(workflow_json: str) -> str:
        workflow = json.loads(workflow_json)
        return json.dumps(_validate_workflow(workflow), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_execute(workflow_json: str, dry_run: bool = False) -> str:
        workflow = json.loads(workflow_json)
        return json.dumps(_execute_workflow(workflow, dry_run=dry_run), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_health() -> str:
        with _client() as client:
            return json.dumps(client.health(), ensure_ascii=False, indent=2)

    return mcp


def _client():
    from nlp2dsl_sdk.client import NLP2DSLClient

    return NLP2DSLClient.from_env()


def _plan_workflow(text: str, mode: str = "auto") -> dict[str, Any]:
    import httpx
    import os

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
    import os

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
    import os

    backend = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
    resp = httpx.post(
        f"{backend}/workflow/execute",
        json={"workflow": workflow, "dry_run": dry_run},
        timeout=float(os.getenv("NLP2DSL_TIMEOUT", "60")),
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    mcp = build_mcp()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
