"""Convert nlp2cmd KeywordIntentDetector results to IntentIR."""

from __future__ import annotations

from typing import Any

from pact_ir import Ambiguity, EntityBag, IntentIR

from nlp2cmd_intent.domain_mapping import domain_to_target_kind, intent_to_execution_risk


def detection_to_intent_ir(result: Any, *, query: str = "") -> IntentIR:
    """Map nlp2cmd DetectionResult (or compatible object) to IntentIR."""
    domain = str(getattr(result, "domain", "unknown") or "unknown")
    intent = str(getattr(result, "intent", "unknown") or "unknown")
    confidence = float(getattr(result, "confidence", 0.0) or 0.0)
    matched = bool(getattr(result, "matched", confidence >= 0.5))
    entities_raw = getattr(result, "entities", None) or {}
    metadata_raw = getattr(result, "metadata", None) or {}
    matched_keyword = str(getattr(result, "matched_keyword", "") or "")

    ambiguities: list[Ambiguity] = []
    if not matched:
        ambiguities.append(
            Ambiguity(
                field="intent",
                message="keyword detector below confidence threshold",
                candidates=[intent] if intent != "unknown" else [],
            )
        )

    return IntentIR(
        query=query or str(metadata_raw.get("query", "")),
        intent=intent,
        domain=domain,
        entities=EntityBag(values=dict(entities_raw)),
        target_kind=domain_to_target_kind(domain),
        constraints={"matched": matched},
        confidence=confidence,
        ambiguities=ambiguities,
        execution_risk=intent_to_execution_risk(intent, domain=domain),
        metadata={
            **dict(metadata_raw),
            "matched_keyword": matched_keyword,
            "source": "nlp2cmd_intent.KeywordIntentDetector",
        },
    )
