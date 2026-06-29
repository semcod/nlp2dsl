"""Read-only query handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsl2nlp2dsl.result import DslResult


def _client():
    from nlp2dsl_sdk.client import NLP2DSLClient

    return NLP2DSLClient.from_env()


def _load_workflow(cmd: dict[str, Any]) -> dict[str, Any] | None:
    if wf := cmd.get("workflow"):
        return dict(wf)
    if path := cmd.get("workflow_file"):
        text = Path(path).expanduser().read_text(encoding="utf-8")
        return json.loads(text) if path.endswith(".json") else __import__("yaml").safe_load(text)
    return None


def handle_orient(cmd: dict[str, Any], *, line: str) -> DslResult:
    text = cmd.get("text", "")
    mode = cmd.get("mode", "auto")
    try:
        with _client() as client:
            data = client._nlp_service("post", "/nlp/orient", json={"text": text, "mode": mode}).json()
        return DslResult(ok=True, command=line, action="orient", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="orient", error=str(exc))


def handle_parse(cmd: dict[str, Any], *, line: str) -> DslResult:
    text = cmd.get("text", "")
    mode = cmd.get("mode", "auto")
    try:
        with _client() as client:
            data = client._nlp_service("post", "/nlp/parse", json={"text": text, "mode": mode}).json()
        return DslResult(ok=True, command=line, action="parse", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="parse", error=str(exc))


def handle_plan(cmd: dict[str, Any], *, line: str) -> DslResult:
    text = cmd.get("text", "")
    mode = cmd.get("mode", "auto")
    try:
        with _client() as client:
            data = client._backend("post", "/workflow/plan", json={"text": text, "mode": mode}).json()
        ok = data.get("status") not in {"validation_failed", "blocked", "failed"}
        return DslResult(ok=ok, command=line, action="plan", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="plan", error=str(exc))


def handle_validate(cmd: dict[str, Any], *, line: str) -> DslResult:
    workflow = _load_workflow(cmd)
    if workflow is None and cmd.get("text"):
        plan = handle_plan({"verb": "PLAN", "text": cmd["text"], "mode": cmd.get("mode", "auto")}, line=line)
        if not plan.ok:
            return plan
        workflow = (plan.data or {}).get("workflow")
    if workflow is None:
        return DslResult(ok=False, command=line, action="validate", error="VALIDATE requires workflow, workflow_file or text")
    try:
        with _client() as client:
            data = client.workflow_validate(workflow, check_policy=bool(cmd.get("check_policy")))
        ok = data.get("status") not in {"validation_failed", "blocked", "failed"}
        return DslResult(ok=ok, command=line, action="validate", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="validate", error=str(exc))


def handle_health(cmd: dict[str, Any], *, line: str) -> DslResult:
    try:
        with _client() as client:
            data = client.health()
        return DslResult(ok=True, command=line, action="health", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="health", error=str(exc))


def handle_actions(cmd: dict[str, Any], *, line: str) -> DslResult:
    try:
        with _client() as client:
            data = client.workflow_actions()
        return DslResult(ok=True, command=line, action="actions", output=json.dumps(data, ensure_ascii=False, indent=2), data={"actions": data})
    except Exception as exc:
        return DslResult(ok=False, command=line, action="actions", error=str(exc))


def handle_resolve(cmd: dict[str, Any], *, line: str) -> DslResult:
    try:
        from uri2nlp2dsl.resolve import resolve_nl
    except ImportError as exc:
        return DslResult(ok=False, command=line, action="resolve", error=f"uri2nlp2dsl required: {exc}")

    hits = resolve_nl(cmd.get("text", ""))
    payload = [h.to_dict() for h in hits]
    return DslResult(
        ok=bool(hits),
        command=line,
        action="resolve",
        output=json.dumps(payload, ensure_ascii=False, indent=2),
        data={"hits": payload},
        error=None if hits else "no URI matches",
    )
