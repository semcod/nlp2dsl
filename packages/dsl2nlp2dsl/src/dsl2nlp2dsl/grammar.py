"""Text DSL → dict (JSON-like command)."""

from __future__ import annotations

import json
import re
import shlex
from typing import Any


def _split_command(line: str) -> list[str]:
    line = line.strip()
    if not line or line.startswith("#"):
        return []
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return line.split()


def _pick_flag(tokens: list[str], flag: str) -> str | None:
    upper = flag.upper()
    for i, tok in enumerate(tokens):
        if tok.upper() == upper and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _quoted_or_rest(tokens: list[str], start: int = 0) -> str:
    if start >= len(tokens):
        return ""
    first = tokens[start]
    if first.startswith('"') or first.startswith("'"):
        return first.strip("\"'")
    parts: list[str] = []
    for tok in tokens[start:]:
        if tok.upper() in {"MODE", "FILE", "OUT", "WITH", "TO", "DEST", "DRY_RUN", "CHECK_POLICY", "PROFILE", "STATUS"}:
            break
        parts.append(tok)
    return " ".join(parts)


def parse_line(line: str) -> dict[str, Any] | None:
    """Parse one DSL line into a command dict."""
    tokens = _split_command(line)
    if not tokens:
        return None

    verb = tokens[0].upper()
    rest = tokens[1:]
    cmd: dict[str, Any] = {"verb": verb}

    if verb in {"PARSE", "PLAN", "ORIENT", "GENERATE", "RESOLVE", "CHAT"}:
        cmd["text"] = _quoted_or_rest(rest)
        mode = _pick_flag(rest, "MODE")
        if mode:
            cmd["mode"] = mode.lower()
        out = _pick_flag(rest, "OUT")
        if out:
            cmd["out"] = out

    elif verb == "VALIDATE":
        wf_file = _pick_flag(rest, "FILE")
        if wf_file:
            cmd["workflow_file"] = wf_file
        elif rest:
            candidate = rest[0]
            if candidate.endswith(".json") or candidate.endswith(".yaml"):
                cmd["workflow_file"] = candidate
            else:
                cmd["text"] = _quoted_or_rest(rest)
        if _pick_flag(rest, "CHECK_POLICY"):
            cmd["check_policy"] = True

    elif verb in {"EXECUTE", "SIMULATE"}:
        text = _quoted_or_rest(rest)
        if text and not text.endswith((".json", ".yaml")):
            cmd["text"] = text
        wf_file = _pick_flag(rest, "FILE")
        if wf_file:
            cmd["workflow_file"] = wf_file
        elif rest and rest[0].endswith((".json", ".yaml")):
            cmd["workflow_file"] = rest[0]
        mode = _pick_flag(rest, "MODE")
        if mode:
            cmd["mode"] = mode.lower()
        if _pick_flag(rest, "DRY_RUN"):
            cmd["dry_run"] = True

    elif verb == "DRAFT":
        cmd["name"] = rest[0] if rest else ""
        status = _pick_flag(rest, "STATUS")
        if status:
            cmd["status"] = status
        path = _pick_flag(rest, "FILE")
        if path:
            cmd["draft_file"] = path

    elif verb == "OBSERVE":
        cmd["target"] = rest[0] if rest else "."

    elif verb == "COMPOSE":
        cmd["profile"] = _pick_flag(rest, "PROFILE") or (rest[0] if rest else "default")
        out = _pick_flag(rest, "OUT")
        if out:
            cmd["out"] = out

    elif verb in {"HEALTH", "ACTIONS"}:
        pass

    elif verb == "QUERY":
        cmd["target"] = rest[0] if rest else ""
        file_param = _pick_flag(rest, "FILE")
        if file_param:
            cmd["file"] = file_param
        fmt = _pick_flag(rest, "FORMAT")
        if fmt:
            cmd["format"] = fmt.lower()

    else:
        cmd["args"] = rest

    return cmd


def to_text(cmd: dict[str, Any]) -> str:
    """Serialize command dict back to canonical DSL line."""
    verb = str(cmd.get("verb", "")).upper()
    parts = [verb]

    if text := cmd.get("text"):
        parts.append(json.dumps(text) if " " in text else f'"{text}"')
    if target := cmd.get("target"):
        parts.append(str(target))
    if name := cmd.get("name"):
        parts.append(str(name))
    if wf := cmd.get("workflow_file"):
        parts.append("FILE")
        parts.append(str(wf))
    if mode := cmd.get("mode"):
        parts.extend(["MODE", str(mode)])
    if out := cmd.get("out"):
        parts.extend(["OUT", str(out)])
    if cmd.get("dry_run"):
        parts.extend(["DRY_RUN", "true"])
    if cmd.get("check_policy"):
        parts.extend(["CHECK_POLICY", "true"])
    if profile := cmd.get("profile"):
        parts.extend(["PROFILE", str(profile)])

    return " ".join(parts)
