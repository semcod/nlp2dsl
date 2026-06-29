"""Dict ↔ protobuf DslEnvelope / DslResult."""

from __future__ import annotations

import json
from typing import Any

from dsl2nlp2dsl.v1 import command_pb2, result_pb2
from dsl2nlp2dsl.grammar import parse_line, to_text
from dsl2nlp2dsl.result import DslResult

_BODY_MAP: dict[str, str] = {
    "PARSE": "parse",
    "PLAN": "plan",
    "VALIDATE": "validate",
    "EXECUTE": "execute",
    "GENERATE": "generate",
    "DRAFT": "draft",
    "OBSERVE": "observe",
    "COMPOSE": "compose",
    "HEALTH": "health",
    "ACTIONS": "actions",
    "RESOLVE": "resolve",
    "ORIENT": "orient",
    "SIMULATE": "simulate",
    "CHAT": "chat",
}


def _set_body(envelope: command_pb2.DslEnvelope, cmd: dict[str, Any]) -> None:
    verb = str(cmd.get("verb", "")).upper()
    field = _BODY_MAP.get(verb)
    if not field:
        return
    msg = getattr(envelope, field)
    if verb in {"PARSE", "PLAN", "ORIENT", "GENERATE", "RESOLVE", "CHAT"}:
        msg.text = str(cmd.get("text", ""))
        if hasattr(msg, "mode"):
            msg.mode = str(cmd.get("mode", "auto"))
    elif verb == "VALIDATE":
        msg.workflow_file = str(cmd.get("workflow_file", ""))
        msg.text = str(cmd.get("text", ""))
        msg.check_policy = bool(cmd.get("check_policy"))
    elif verb in {"EXECUTE", "SIMULATE"}:
        msg.text = str(cmd.get("text", ""))
        msg.workflow_file = str(cmd.get("workflow_file", ""))
        msg.mode = str(cmd.get("mode", "auto"))
        msg.dry_run = bool(cmd.get("dry_run"))
    elif verb == "DRAFT":
        msg.name = str(cmd.get("name", ""))
        msg.status = str(cmd.get("status", ""))
        msg.draft_file = str(cmd.get("draft_file", ""))
    elif verb == "OBSERVE":
        msg.target = str(cmd.get("target", "."))
    elif verb == "COMPOSE":
        msg.profile = str(cmd.get("profile", "default"))
        msg.out = str(cmd.get("out", ""))
        msg.target = str(cmd.get("target", "."))


def dict_to_envelope(cmd: dict[str, Any], *, default_file: str = "", correlation_id: str = "") -> command_pb2.DslEnvelope:
    envelope = command_pb2.DslEnvelope()
    envelope.verb = str(cmd.get("verb", "")).upper()
    _set_body(envelope, cmd)
    envelope.default_file = default_file
    envelope.correlation_id = correlation_id
    return envelope


def envelope_to_dict(envelope: command_pb2.DslEnvelope) -> dict[str, Any]:
    verb = envelope.verb.upper()
    cmd: dict[str, Any] = {"verb": verb}
    field = _BODY_MAP.get(verb)
    if not field:
        return cmd
    which = envelope.WhichOneof("body")
    if which != field:
        return cmd
    msg = getattr(envelope, field)
    if verb in {"PARSE", "PLAN", "ORIENT", "GENERATE", "RESOLVE", "CHAT"}:
        if msg.text:
            cmd["text"] = msg.text
        if getattr(msg, "mode", ""):
            cmd["mode"] = msg.mode
    elif verb == "VALIDATE":
        if msg.workflow_file:
            cmd["workflow_file"] = msg.workflow_file
        if msg.text:
            cmd["text"] = msg.text
        if msg.check_policy:
            cmd["check_policy"] = True
    elif verb in {"EXECUTE", "SIMULATE"}:
        if msg.text:
            cmd["text"] = msg.text
        if msg.workflow_file:
            cmd["workflow_file"] = msg.workflow_file
        if msg.mode:
            cmd["mode"] = msg.mode
        if msg.dry_run:
            cmd["dry_run"] = True
    elif verb == "DRAFT":
        if msg.name:
            cmd["name"] = msg.name
        if msg.status:
            cmd["status"] = msg.status
        if msg.draft_file:
            cmd["draft_file"] = msg.draft_file
    elif verb == "OBSERVE":
        cmd["target"] = msg.target or "."
    elif verb == "COMPOSE":
        if msg.profile:
            cmd["profile"] = msg.profile
        if msg.out:
            cmd["out"] = msg.out
        if msg.target:
            cmd["target"] = msg.target
    return cmd


def encode_protobuf(cmd: dict[str, Any], *, default_file: str = "", correlation_id: str = "") -> bytes:
    envelope = dict_to_envelope(cmd, default_file=default_file, correlation_id=correlation_id)
    return envelope.SerializeToString()


def decode_protobuf(data: bytes) -> dict[str, Any]:
    envelope = command_pb2.DslEnvelope()
    envelope.ParseFromString(data)
    return envelope_to_dict(envelope)


def encode_text_to_protobuf(line: str, *, default_file: str = "", correlation_id: str = "") -> bytes:
    cmd = parse_line(line)
    if cmd is None:
        raise ValueError("empty command")
    return encode_protobuf(cmd, default_file=default_file, correlation_id=correlation_id)


def decode_protobuf_to_text(data: bytes) -> str:
    return to_text(decode_protobuf(data))


def result_to_pb(result: DslResult) -> result_pb2.DslResult:
    pb = result_pb2.DslResult()
    pb.ok = result.ok
    pb.verb = result.action.upper() if result.action else ""
    pb.output = result.output
    pb.data_json = json.dumps(result.data, ensure_ascii=False).encode("utf-8")
    pb.error = result.error or ""
    pb.event_id = result.event_id or ""
    pb.command = result.command
    pb.action = result.action
    return pb


def pb_to_result(pb: result_pb2.DslResult) -> DslResult:
    data: dict[str, Any] = {}
    if pb.data_json:
        try:
            data = json.loads(pb.data_json.decode("utf-8"))
        except json.JSONDecodeError:
            data = {}
    return DslResult(
        ok=pb.ok,
        command=pb.command,
        action=pb.action,
        output=pb.output,
        data=data,
        error=pb.error or None,
        event_id=pb.event_id or None,
    )


def encode_result_protobuf(result: DslResult) -> bytes:
    return result_to_pb(result).SerializeToString()


def decode_result_protobuf(data: bytes) -> DslResult:
    pb = result_pb2.DslResult()
    pb.ParseFromString(data)
    return pb_to_result(pb)
