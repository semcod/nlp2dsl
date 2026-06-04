"""Log-based metryki i audyt decyzji routingu (Faza 3)."""

from __future__ import annotations

import logging
from collections import Counter
from threading import Lock

from app.routing.intent import IntentDecision

log = logging.getLogger("nlp.routing")

_COUNTERS: Counter[str] = Counter()
_LOCK = Lock()

_COUNTER_BY_SOURCE = {
    "native_routing": "native_hit",
    "action_aliases": "native_hit",
    "rules": "rules_hit",
    "llm": "llm_hit",
}


def record_intent_decision(decision: IntentDecision) -> None:
    """Inkrementuje liczniki i loguje strukturalną decyzję."""
    with _LOCK:
        source_key = _COUNTER_BY_SOURCE.get(decision.source)
        if source_key:
            _COUNTERS[source_key] += 1
        if not decision.authorized:
            _COUNTERS["authorize_deny"] += 1
        if decision.intent == "unknown" or decision.action == "unknown":
            _COUNTERS["unknown_intent"] += 1
        if decision.source == "unknown" or decision.reason_codes == ["empty_message"]:
            _COUNTERS["empty_message"] += 1

    log.info(
        "intent_decision action=%s source=%s conf=%.2f authorized=%s codes=%s",
        decision.action,
        decision.source,
        decision.confidence,
        decision.authorized,
        ",".join(decision.reason_codes),
        extra={"intent_decision": decision.to_dict()},
    )


def routing_metrics_snapshot() -> dict[str, int]:
    """Snapshot liczników (np. /health.routing_metrics)."""
    with _LOCK:
        return dict(_COUNTERS)


def reset_routing_metrics() -> None:
    """Tylko testy."""
    with _LOCK:
        _COUNTERS.clear()
