"""Dict ↔ validate via JSON Schema."""

from __future__ import annotations

from typing import Any

import jsonschema

from dsl2nlp2dsl.grammar import parse_line, to_text
from dsl2nlp2dsl.schema_registry import schema_for_verb


def validate_command(cmd: dict[str, Any]) -> list[str]:
    verb = str(cmd.get("verb", "")).upper()
    schema = schema_for_verb(verb)
    if schema is None:
        return []
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{e.message}" for e in sorted(validator.iter_errors(cmd), key=str)]


def encode_text(line: str) -> tuple[dict[str, Any], list[str]]:
    cmd = parse_line(line)
    if cmd is None:
        return {}, ["empty command"]
    errors = validate_command(cmd)
    return cmd, errors


def decode_text(line: str) -> dict[str, Any]:
    cmd, errors = encode_text(line)
    if errors:
        raise ValueError("; ".join(errors))
    return cmd


def roundtrip_text(line: str) -> str:
    cmd = decode_text(line)
    return to_text(cmd)


def encode_protobuf(line: str, *, default_file: str = "", correlation_id: str = "") -> bytes:
    from dsl2nlp2dsl.pb_codec import encode_text_to_protobuf

    return encode_text_to_protobuf(line, default_file=default_file, correlation_id=correlation_id)


def decode_protobuf(data: bytes) -> str:
    from dsl2nlp2dsl.pb_codec import decode_protobuf_to_text

    return decode_protobuf_to_text(data)


def roundtrip_protobuf(line: str) -> str:
    return decode_protobuf(encode_protobuf(line))
