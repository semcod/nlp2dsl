"""Backward-compat shim — use app.routing.parser.llm."""

from app.routing.parser.llm import LLM_MODEL, _detect_provider, parse_llm

__all__ = ["LLM_MODEL", "_detect_provider", "parse_llm"]
