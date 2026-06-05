"""Tests for LLM entity enrichment (Phase B)."""

from __future__ import annotations

import pytest
from app.dsl.pipeline import map_to_dsl_with_enrichment
from app.routing.parser.enrich import (
    can_enrich_missing,
    enrich_entities,
    get_enrichable_missing,
    is_enrich_enabled,
)
from app.schemas import NLPEntities, NLPIntent, NLPResult


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


@pytest.fixture
def _enable_enrich(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NLP_ENRICH_MISSING", "1")
    monkeypatch.setattr(
        "app.routing.parser.enrich._detect_provider",
        lambda: "openrouter",
    )


class TestEnrichHelpers:
    def test_is_enrich_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NLP_ENRICH_MISSING", "1")
        assert is_enrich_enabled() is True
        monkeypatch.setenv("NLP_ENRICH_MISSING", "0")
        assert is_enrich_enabled() is False

    def test_get_enrichable_missing_body_only(self) -> None:
        missing = ["send_email.body"]
        assert get_enrichable_missing(missing) == ["send_email.body"]

    def test_get_enrichable_missing_ignores_required(self) -> None:
        missing = ["send_invoice.amount", "send_invoice.to"]
        assert get_enrichable_missing(missing) == []

    def test_can_enrich_only_quality_fields(self, _enable_enrich: None) -> None:
        assert can_enrich_missing(["send_email.body"]) is True
        assert can_enrich_missing(["notify_slack.message"]) is True
        assert can_enrich_missing(["send_email.body", "send_invoice.to"]) is False


class TestEnrichEntities:
    @pytest.mark.asyncio
    async def test_enrich_fills_email_body(
        self, _enable_enrich: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def fake_acompletion(**_kwargs: object) -> _FakeResponse:
            return _FakeResponse(
                '{"subject": "Status projektu", '
                '"message": "Dzień dobry, przesyłam aktualny status projektu."}'
            )

        monkeypatch.setattr("app.routing.parser.enrich.acompletion", fake_acompletion)

        nlp = NLPResult(
            intent=NLPIntent(intent="send_email", confidence=0.9),
            entities=NLPEntities(to="team@firma.pl", subject="Status projektu"),
            raw_text="Wyślij email do team@firma.pl z tematem Status projektu",
        )
        enriched = await enrich_entities(nlp, ["send_email.body"])
        assert enriched is not None
        assert enriched.entities.message == "Dzień dobry, przesyłam aktualny status projektu."

    @pytest.mark.asyncio
    async def test_enrich_disabled_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NLP_ENRICH_MISSING", "0")
        nlp = NLPResult(
            intent=NLPIntent(intent="send_email", confidence=0.9),
            entities=NLPEntities(to="team@firma.pl", subject="Status"),
            raw_text="Wyślij email",
        )
        assert await enrich_entities(nlp, ["send_email.body"]) is None


    @pytest.mark.asyncio
    async def test_enrich_fills_notify_message(
        self, _enable_enrich: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def fake_acompletion(**_kwargs: object) -> _FakeResponse:
            return _FakeResponse('{"message": "Deploy produkcji zakończony pomyślnie."}')

        monkeypatch.setattr("app.routing.parser.enrich.acompletion", fake_acompletion)

        nlp = NLPResult(
            intent=NLPIntent(intent="notify_slack", confidence=0.9),
            entities=NLPEntities(channel="#devops"),
            raw_text="Powiadom #devops o zakończeniu deployu",
        )
        enriched = await enrich_entities(nlp, ["notify_slack.message"])
        assert enriched is not None
        assert "deploy" in enriched.entities.message.lower()


class TestEnrichPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_completes_after_enrich(
        self, _enable_enrich: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def fake_acompletion(**_kwargs: object) -> _FakeResponse:
            return _FakeResponse(
                '{"message": "Przypominamy o statusie projektu i prosimy o informację zwrotną."}'
            )

        monkeypatch.setattr("app.routing.parser.enrich.acompletion", fake_acompletion)

        nlp = NLPResult(
            intent=NLPIntent(intent="send_email", confidence=0.9),
            entities=NLPEntities(to="jan@example.com", subject="Status"),
            raw_text="Wyślij email do jan@example.com z tematem Status",
        )
        dialog = await map_to_dsl_with_enrichment(nlp)
        assert dialog.status == "complete"
        assert dialog.workflow is not None
        step = dialog.workflow.steps[0]
        assert step.action == "send_email"
        assert step.config["body"]
