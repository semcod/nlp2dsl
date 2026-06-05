"""Parser mode resolution — rules / llm / auto with fallbacks."""

from __future__ import annotations

import logging
import os

from app.routing.parser.llm import _detect_provider, parse_llm
from app.routing.parser.rules import parse_rules
from app.schemas import NLPResult

log = logging.getLogger("nlp.parser")

_FALLBACK_THRESHOLD = float(os.getenv("LLM_FALLBACK_THRESHOLD", "0.5"))


async def parse_with_mode(text: str, mode: str) -> NLPResult:
    mode = mode.lower().strip()

    if mode == "rules":
        return parse_rules(text)

    if mode == "llm":
        if _detect_provider() == "none":
            return parse_rules(text)
        llm_result = await parse_llm(text)
        if llm_result.intent.intent != "unknown":
            return llm_result
        rules_result = parse_rules(text)
        if rules_result.intent.intent != "unknown":
            log.info("LLM returned unknown; using rules fallback")
            return rules_result
        return llm_result

    # auto
    rules_result = parse_rules(text)
    if rules_result.intent.confidence >= _FALLBACK_THRESHOLD:
        return rules_result
    if _detect_provider() == "none":
        return rules_result
    try:
        llm_result = await parse_llm(text)
        if llm_result.intent.confidence > rules_result.intent.confidence:
            return llm_result
    except Exception:
        log.exception("LLM fallback failed in auto mode")
    return rules_result
