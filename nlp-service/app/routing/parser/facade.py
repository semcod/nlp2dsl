"""
Jednolity punkt parsowania NLP — używany przez /nlp/* i orchestrator (chat).
"""

from __future__ import annotations

import os

from app.routing.parser.resolve_mode import parse_with_mode
from app.schemas import NLPResult


async def parse_text(text: str, mode: str | None = None) -> NLPResult:
    """
    mode: rules | llm | auto
    Domyślnie NLP_CHAT_MODE lub auto.
    """
    resolved = (mode or os.getenv("NLP_CHAT_MODE", "auto")).lower().strip()
    return await parse_with_mode(text, resolved)
