"""Merge NLP parse results into conversation state."""

from __future__ import annotations

from app.registry import get_trigger
from app.schemas import ConversationState, NLPResult

_MIN_INTENT_CONFIDENCE: float = 0.5


def merge_into_state(state: ConversationState, nlp: NLPResult) -> None:
    """Merge NLP result into conversation state (accumulate entities)."""
    if nlp.intent.intent != "unknown":
        if state.intent is None or nlp.intent.confidence > _MIN_INTENT_CONFIDENCE:
            state.intent = nlp.intent.intent

    new_entities = nlp.entities.model_dump(exclude_none=True)
    for key, value in new_entities.items():
        if value is not None:
            state.entities[key] = value

    full_text = " ".join(h["text"] for h in state.history if h["role"] == "user")
    trigger = get_trigger(full_text)
    if trigger != "manual":
        state.entities["_trigger"] = trigger
