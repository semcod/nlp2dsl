"""Thin adapter — LLM draft operations via dsl2nlp2dsl.dispatch()."""

from __future__ import annotations

from typing import Any


def dispatch_draft(name: str, *, status: str | None = None, draft_file: str | None = None) -> dict[str, Any]:
    from dsl2nlp2dsl import dispatch

    parts = ["DRAFT", name]
    if status:
        parts.extend(["STATUS", status])
    if draft_file:
        parts.extend(["FILE", draft_file])
    result = dispatch(" ".join(parts))
    return result.to_dict()
