"""Intent clarification enforcement for low-confidence queries."""

from __future__ import annotations

import os

from pact_ir import IntentIR


class IntentClarificationRequired(Exception):
    """Raised when IntentIR needs user clarification before planning."""

    def __init__(self, intent: IntentIR) -> None:
        self.intent = intent
        messages: list[str] = []
        for ambiguity in intent.ambiguities:
            messages.append(ambiguity.message)
        if intent.confidence < 0.5:
            messages.append(f"confidence {intent.confidence:.2f} below threshold 0.5")
        super().__init__("; ".join(messages) or "intent needs clarification")


def clarification_enforced() -> bool:
    return os.getenv("NLP2CMD_ENFORCE_CLARIFICATION", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def ensure_intent_clear(intent: IntentIR, *, enforced: bool | None = None) -> None:
    """Raise IntentClarificationRequired when clarification is required."""
    if enforced is None:
        enforced = clarification_enforced()
    if enforced and intent.needs_clarification():
        raise IntentClarificationRequired(intent)
