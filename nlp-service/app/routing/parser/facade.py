"""
Jednolity punkt parsowania NLP — używany przez /nlp/* i orchestrator (chat).
"""

from __future__ import annotations

import os

from app.routing.parser.llm import _detect_provider, parse_llm
from app.routing.parser.rules import parse_rules
from app.schemas import NLPResult

_FALLBACK_THRESHOLD = float(os.getenv("LLM_FALLBACK_THRESHOLD", "0.5"))


async def parse_text(text: str, mode: str | None = None) -> NLPResult:
    """
    mode: rules | llm | auto
    Domyślnie NLP_CHAT_MODE lub auto.
    """
    mode = (mode or os.getenv("NLP_CHAT_MODE", "auto")).lower().strip()

    if mode == "rules":
        return parse_rules(text)
    if mode == "llm":
        return await parse_llm(text)

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
        pass
    return rules_result
