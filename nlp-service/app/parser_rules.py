"""Backward-compat shim — use app.routing.parser.rules."""

from app.routing.parser.rules import parse_rules

__all__ = ["parse_rules"]
