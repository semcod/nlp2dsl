"""Thin adapter — stack compose via dsl2nlp2dsl COMPOSE."""

from __future__ import annotations

from typing import Any


def dispatch_compose(profile: str = "default", *, out: str | None = None, target: str = ".") -> dict[str, Any]:
    from dsl2nlp2dsl import dispatch

    line = f"COMPOSE PROFILE {profile}"
    if out:
        line += f" OUT {out}"
    return dispatch(line).to_dict()
