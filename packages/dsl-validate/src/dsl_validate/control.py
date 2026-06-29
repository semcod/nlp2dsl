"""Thin adapter — validation via dsl2nlp2dsl VALIDATE command."""

from __future__ import annotations

from typing import Any


def dispatch_validate(
    *,
    text: str | None = None,
    workflow_file: str | None = None,
    check_policy: bool = False,
) -> dict[str, Any]:
    from dsl2nlp2dsl import dispatch

    if workflow_file:
        line = f"VALIDATE FILE {workflow_file}"
    elif text:
        line = f'VALIDATE "{text}"'
    else:
        raise ValueError("dispatch_validate requires text or workflow_file")
    if check_policy:
        line += " CHECK_POLICY true"
    return dispatch(line).to_dict()
