"""Thin adapter — artifact/registry ops via dsl2nlp2dsl OBSERVE."""

from __future__ import annotations

from typing import Any


def dispatch_observe(target: str = ".") -> dict[str, Any]:
    from dsl2nlp2dsl import dispatch

    return dispatch(f"OBSERVE {target}").to_dict()
