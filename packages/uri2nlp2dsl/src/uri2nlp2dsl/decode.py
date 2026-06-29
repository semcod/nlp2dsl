"""URI → DSL line → dispatch."""

from __future__ import annotations

from dsl2nlp2dsl import DslResult, dispatch
from uri2nlp2dsl.uri import Nlp2dslUri, parse_uri


def uri_to_dsl(uri: str) -> str:
    parsed = parse_uri(uri)
    parts = [parsed.verb]
    if text := parsed.params.get("text"):
        parts.append(f'"{text}"' if " " in text else text)
    for key in ("mode", "file", "out", "profile", "target", "status", "name"):
        if val := parsed.params.get(key):
            parts.extend([key.upper(), val])
    if parsed.params.get("dry_run", "").lower() in {"1", "true", "yes"}:
        parts.extend(["DRY_RUN", "true"])
    if parsed.params.get("check_policy", "").lower() in {"1", "true", "yes"}:
        parts.extend(["CHECK_POLICY", "true"])
    return " ".join(parts)


def decode_uri(uri: str) -> str:
    return uri_to_dsl(uri)


def run_uri(uri: str, *, default_file: str | None = None) -> DslResult:
    line = uri_to_dsl(uri)
    return dispatch(line, default_file=default_file)
