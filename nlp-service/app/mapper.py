"""Backward-compat shim — use app.dsl.mapper."""

from app.dsl.mapper import _resolve_actions, map_to_dsl

__all__ = ["_resolve_actions", "map_to_dsl"]
