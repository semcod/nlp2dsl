"""NLP → DSL pipeline with optional LLM enrichment."""

from __future__ import annotations

import logging

from app.dsl.mapper import map_to_dsl
from app.routing.parser.enrich import enrich_entities
from app.schemas import DialogResponse, NLPResult
from nlp2dsl_sdk.workflow import PlanResult, parse_result_from_nlp, plan_result_from_dialog

log = logging.getLogger("nlp.pipeline")


async def map_to_dsl_with_enrichment(nlp: NLPResult) -> DialogResponse:
    """Map NLP → DSL; optionally enrich quality fields before a second pass."""
    dialog = map_to_dsl(nlp)
    if dialog.status == "complete":
        return dialog

    missing = dialog.missing_fields or []
    if not missing:
        return dialog

    enriched = await enrich_entities(nlp, missing)
    if enriched is None:
        return dialog

    enriched_dialog = map_to_dsl(enriched)
    if enriched_dialog.status == "complete":
        log.info("DSL complete after LLM enrichment")
    return enriched_dialog


async def plan_lifecycle_from_nlp(
    nlp: NLPResult,
    *,
    text: str | None = None,
    mode: str = "auto",
    routing: dict | None = None,
) -> PlanResult:
    """Build a canonical lifecycle plan around the existing mapper."""
    parse = parse_result_from_nlp(
        text if text is not None else nlp.raw_text,
        mode,
        nlp,
        routing=routing,
    )
    dialog = await map_to_dsl_with_enrichment(nlp)
    return plan_result_from_dialog(
        dialog,
        parse=parse,
        source="nlp-service.mapper",
        trace=[
            {"stage": "parse", "status": parse.status, "intent": parse.intent},
            {"stage": "plan", "status": dialog.status},
        ],
    )
