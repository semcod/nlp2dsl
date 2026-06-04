"""Audytowalna decyzja routingu akcji (native / rules / LLM + ACL)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas import NLPEntities, NLPIntent, NLPResult


@dataclass
class IntentDecision:
    """Wynik `resolve_intent` — spójny kontrakt dla orchestratora i Mullm BFF."""

    action: str | None
    intent: str
    confidence: float
    source: str  # native_routing | action_aliases | rules | llm | unknown
    reason_codes: list[str] = field(default_factory=list)
    resource_area: str | None = None
    permission_action: str = "execute"
    uri: str | None = None
    authorized: bool = True
    deny_reason: str | None = None
    deny_effect: str | None = None
    agent_id: str = ""
    candidate_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "intent": self.intent,
            "confidence": self.confidence,
            "source": self.source,
            "reason_codes": self.reason_codes,
            "resource_area": self.resource_area,
            "permission_action": self.permission_action,
            "uri": self.uri,
            "authorized": self.authorized,
            "deny_reason": self.deny_reason,
            "deny_effect": self.deny_effect,
            "agent_id": self.agent_id,
            "candidate_actions": self.candidate_actions,
        }

    def to_nlp_result(self, raw_text: str) -> NLPResult:
        """Mapuje do NLPResult gdy akcja jest dozwolona."""
        action = self.action or self.intent or "unknown"
        return NLPResult(
            intent=NLPIntent(intent=action, confidence=self.confidence),
            entities=NLPEntities(),
            raw_text=raw_text,
        )
