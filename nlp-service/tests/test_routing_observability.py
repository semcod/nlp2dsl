"""Tests for routing observability counters."""

from __future__ import annotations

import pytest

from app.routing.observability import (
    record_intent_decision,
    reset_routing_metrics,
    routing_metrics_snapshot,
)
from app.routing.intent import IntentDecision
from app.routing.resolve import resolve_intent


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    reset_routing_metrics()
    yield
    reset_routing_metrics()


def test_record_increments_rules_hit() -> None:
    record_intent_decision(
        IntentDecision(
            action="send_invoice",
            intent="send_invoice",
            confidence=0.9,
            source="rules",
            reason_codes=["parser_rules"],
        )
    )
    snap = routing_metrics_snapshot()
    assert snap.get("rules_hit", 0) >= 1


@pytest.mark.asyncio
async def test_resolve_intent_updates_metrics() -> None:
    await resolve_intent("Wyślij fakturę na 100 PLN do a@b.pl")
    snap = routing_metrics_snapshot()
    assert snap.get("rules_hit", 0) >= 1 or snap.get("llm_hit", 0) >= 1
