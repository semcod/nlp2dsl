"""Compatibility shim — LLM entity enrichment."""

from app.routing.parser.enrich import (
    can_enrich_missing,
    enrich_entities,
    get_enrichable_missing,
    is_enrich_enabled,
)

__all__ = [
    "can_enrich_missing",
    "enrich_entities",
    "get_enrichable_missing",
    "is_enrich_enabled",
]
