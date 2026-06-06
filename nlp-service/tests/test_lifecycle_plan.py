from __future__ import annotations

import pytest

from app.dsl.pipeline import plan_lifecycle_from_nlp
from app.schemas import NLPEntities, NLPIntent, NLPResult


@pytest.mark.asyncio
async def test_plan_lifecycle_from_nlp_wraps_complete_dsl() -> None:
    nlp = NLPResult(
        intent=NLPIntent(intent="send_invoice", confidence=0.95),
        entities=NLPEntities(amount=1500, currency="PLN", to="klient@firma.pl"),
        raw_text="Wyślij fakturę na 1500 PLN do klient@firma.pl",
    )

    plan = await plan_lifecycle_from_nlp(nlp, text=nlp.raw_text, mode="rules")

    assert plan.status == "complete"
    assert plan.parse is not None
    assert plan.parse.intent == "send_invoice"
    assert plan.workflow is not None
    assert plan.workflow["steps"][0]["action"] == "send_invoice"


@pytest.mark.asyncio
async def test_plan_lifecycle_from_nlp_exposes_missing_fields() -> None:
    nlp = NLPResult(
        intent=NLPIntent(intent="send_invoice", confidence=0.9),
        entities=NLPEntities(amount=1500, currency="PLN"),
        raw_text="Wyślij fakturę na 1500 PLN",
    )

    plan = await plan_lifecycle_from_nlp(nlp, text=nlp.raw_text, mode="rules")

    assert plan.status == "incomplete"
    assert plan.clarification is not None
    assert "send_invoice.to" in plan.missing_fields
