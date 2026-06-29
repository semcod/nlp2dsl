"""CQRS bus — single dispatch entry point."""

from __future__ import annotations

import json
from typing import Any

from dsl2nlp2dsl.codec import validate_command
from dsl2nlp2dsl.events import default_event_store
from dsl2nlp2dsl.grammar import parse_line, to_text
from dsl2nlp2dsl.result import DslResult

QUERY_VERBS = frozenset({"ORIENT", "PARSE", "PLAN", "VALIDATE", "HEALTH", "ACTIONS", "RESOLVE", "QUERY"})
COMMAND_VERBS = frozenset({"EXECUTE", "SIMULATE", "GENERATE", "CHAT", "DRAFT", "OBSERVE", "COMPOSE", "PATCH", "APPEND"})


def _dispatch_cmd(cmd: dict[str, Any], *, line: str, default_file: str | None = None) -> DslResult:
    from dsl2nlp2dsl.handlers import command, query

    verb = str(cmd.get("verb", "")).upper()
    errors = validate_command(cmd)
    if errors:
        return DslResult(ok=False, command=line, action=verb.lower(), error="; ".join(errors))

    handlers = {
        "ORIENT": query.handle_orient,
        "PARSE": query.handle_parse,
        "PLAN": query.handle_plan,
        "VALIDATE": query.handle_validate,
        "HEALTH": query.handle_health,
        "ACTIONS": query.handle_actions,
        "RESOLVE": query.handle_resolve,
        "EXECUTE": command.handle_execute,
        "SIMULATE": command.handle_simulate,
        "GENERATE": command.handle_generate,
        "CHAT": command.handle_chat,
        "DRAFT": command.handle_draft,
        "OBSERVE": command.handle_observe,
        "COMPOSE": command.handle_compose,
    }

    handler = handlers.get(verb)
    if handler is None:
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown command: {verb}")

    result = handler(cmd, line=line)

    if verb in COMMAND_VERBS and result.ok:
        store = default_event_store(default_file or "app.nlp2dsl.less")
        event = store.append(cmd, result.to_dict())
        result.event_id = event.id

    return result


def _bytes_to_cmd(data: bytes) -> tuple[dict[str, Any], str]:
    from dsl2nlp2dsl.pb_codec import decode_protobuf

    try:
        cmd = decode_protobuf(data)
        line = to_text(cmd)
        return cmd, line
    except Exception:
        line = data.decode("utf-8").strip()
        cmd = parse_line(line)
        if cmd is None:
            return {"verb": "NOOP"}, line
        return cmd, line


def dispatch(
    envelope: str | dict[str, Any] | bytes,
    *,
    default_file: str | None = None,
) -> DslResult:
    """Dispatch DSL command from text line, dict, JSON, or protobuf bytes."""
    if isinstance(envelope, bytes):
        cmd, line = _bytes_to_cmd(envelope)
        if cmd.get("verb") == "NOOP":
            return DslResult(ok=True, command=line, action="noop")
        return _dispatch_cmd(cmd, line=line, default_file=default_file)
    if isinstance(envelope, dict):
        line = to_text(envelope)
        return _dispatch_cmd(envelope, line=line, default_file=default_file)
    line = str(envelope).strip()
    cmd = parse_line(line)
    if cmd is None:
        return DslResult(ok=True, command=line, action="noop")
    return _dispatch_cmd(cmd, line=line, default_file=default_file)


def execute_dsl_line(line: str, *, default_file: str | None = None) -> DslResult:
    return dispatch(line, default_file=default_file)


def execute_dsl(text: str, *, default_file: str | None = None) -> list[DslResult]:
    results: list[DslResult] = []
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        results.append(execute_dsl_line(line, default_file=default_file))
    return results
