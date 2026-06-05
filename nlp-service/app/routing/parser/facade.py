"""
Jednolity punkt parsowania NLP — używany przez /nlp/* i orchestrator (chat).
"""

from __future__ import annotations

import os

from app.conversation.system_map import effective_nlp_confidence_min, effective_nlp_parser_mode
from app.routing.parser.resolve_mode import parse_with_mode
from app.schemas import NLPResult


async def parse_text(text: str, mode: str | None = None) -> NLPResult:
    """
    mode: rules | llm | auto
    Domyślnie DOQL process.nlp_parser lub NLP_CHAT_MODE.
    """
    resolved = (mode or effective_nlp_parser_mode() or os.getenv("NLP_CHAT_MODE", "auto")).lower().strip()
    return await parse_with_mode(text, resolved, confidence_min=effective_nlp_confidence_min())
