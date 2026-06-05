"""ExecutionPlanIR → Propact markdown."""

from __future__ import annotations

import json
from typing import Any

import yaml

from pact_ir import ExecutionPlanIR, PlanStep, TargetKind

_DELEGATE_KINDS = frozenset(
    {
        TargetKind.BROWSER,
        TargetKind.DESKTOP,
        TargetKind.SQL,
        TargetKind.UNKNOWN,
    }
)


def _shell_block(dsl: str) -> str:
    body = dsl.strip()
    return f"```propact:shell\n{body}\n```"


def _rest_block(method: str, endpoint: str, body: str = "") -> str:
    lines = [f"{method.upper()} {endpoint}"]
    if body.strip():
        lines.append(body.strip())
    return "```propact:rest\n" + "\n".join(lines) + "\n```"


def _format_json_body(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, indent=2)


def _mcp_block(step: PlanStep) -> str:
    payload = step.params.get("payload")
    if payload is not None:
        body = _format_json_body(payload)
    elif step.dsl.strip():
        body = step.dsl.strip()
    else:
        tool = step.params.get("tool") or step.params.get("name")
        arguments = step.params.get("arguments", step.params.get("args", {}))
        method = str(step.params.get("method", "tools/call"))
        if tool:
            payload = {
                "method": method,
                "params": {"name": str(tool), "arguments": arguments or {}},
            }
        else:
            payload = {"method": method, "params": dict(step.params)}
        body = _format_json_body(payload)
    return f"```propact:mcp\n{body}\n```"


def _ws_block(step: PlanStep) -> str:
    payload = step.params.get("payload")
    if payload is not None:
        body = _format_json_body(payload)
    elif step.dsl.strip():
        body = step.dsl.strip()
    else:
        message = {
            "type": str(step.params.get("type", "message")),
            "url": step.params.get("url"),
            "data": step.params.get("data", step.params.get("message", step.params)),
        }
        body = _format_json_body({k: v for k, v in message.items() if v is not None})
    return f"```propact:ws\n{body}\n```"


def _delegate_block(step: PlanStep) -> str:
    """Marker for nlp2cmd hybrid executor — not executed by Propact CLI."""
    data: dict[str, Any] = {
        "target_kind": step.target_kind.value,
        "action": step.action,
        "id": step.id,
        "description": step.description,
        "risk": step.risk.value,
    }
    if step.dsl.strip():
        data["dsl"] = step.dsl.strip()
    if step.params:
        data["params"] = step.params
    if step.metadata:
        data["metadata"] = step.metadata
    body = yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()
    return f"```propact:delegate\n{body}\n```"


def step_to_propact_block(step: PlanStep) -> str:
    """Render a single plan step as a Propact or delegate fenced block."""
    protocol = step.target_kind.propact_protocol
    if step.target_kind == TargetKind.SHELL or protocol == "shell":
        return _shell_block(step.dsl or str(step.params.get("command", "")))
    if step.target_kind == TargetKind.REST or protocol == "rest":
        method = str(step.params.get("method", "GET"))
        endpoint = str(step.params.get("endpoint", step.params.get("url", "/")))
        body = step.params.get("body", "")
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False)
        return _rest_block(method, endpoint, str(body))
    if step.target_kind == TargetKind.MCP or protocol == "mcp":
        return _mcp_block(step)
    if step.target_kind == TargetKind.WS or protocol == "ws":
        return _ws_block(step)
    if step.target_kind in _DELEGATE_KINDS:
        return _delegate_block(step)
    return _delegate_block(step)


def plan_to_propact_markdown(plan: ExecutionPlanIR) -> str:
    """Render an execution plan as Propact markdown document."""
    header = [
        "---",
        f"query: {plan.query!r}",
        f"source: {plan.source}",
        f"confidence: {plan.confidence}",
        f"format: {plan.format}",
        "---",
        "",
        f"# Plan: {plan.query}",
        "",
    ]
    blocks: list[str] = []
    for step in plan.steps:
        blocks.append(step_to_propact_block(step))
        blocks.append("")
    return "\n".join(header + blocks)
