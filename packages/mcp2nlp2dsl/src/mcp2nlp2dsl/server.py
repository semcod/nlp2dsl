"""Stdio MCP server — thin wrappers over dsl2nlp2dsl."""

from __future__ import annotations

import json
from typing import Any


def _require_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ImportError as exc:
        raise RuntimeError("MCP support requires: pip install mcp2nlp2dsl") from exc


def build_mcp(name: str = "nlp2dsl") -> Any:
    FastMCP = _require_fastmcp()
    from dsl2nlp2dsl import dispatch, execute_dsl, execute_dsl_line
    from nlp2nlp2dsl.to_dsl import to_dsl

    mcp = FastMCP(name)

    @mcp.tool()
    def nlp2dsl_run_dsl(script: str, default_file: str = "") -> str:
        """Execute multi-line NLP2DSL control DSL."""
        results = execute_dsl(script, default_file=default_file or None)
        return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_run_command(command: str, default_file: str = "") -> str:
        """Execute a single NLP2DSL control DSL command."""
        result = execute_dsl_line(command, default_file=default_file or None)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_run_command_json(envelope_json: str, default_file: str = "") -> str:
        """Execute command from JSON dict envelope."""
        envelope = json.loads(envelope_json)
        result = dispatch(envelope, default_file=default_file or None)
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

    @mcp.tool()
    def nlp2dsl_run_command_pb(envelope_bytes: bytes, default_file: str = "") -> bytes:
        """Execute command from protobuf DslEnvelope bytes; returns DslResult protobuf."""
        from dsl2nlp2dsl.pb_codec import encode_result_protobuf

        result = dispatch(envelope_bytes, default_file=default_file or None)
        return encode_result_protobuf(result)

    @mcp.tool()
    def nlp2dsl_to_dsl(prompt: str, mode: str = "auto") -> str:
        """Convert natural language to DSL line (no side effects)."""
        return to_dsl(prompt, mode=mode)

    return mcp


def run_server() -> None:
    build_mcp().run(transport="stdio")
