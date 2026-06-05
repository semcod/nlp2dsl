"""Tests for app.routing.resolve_intent."""

from __future__ import annotations

import pytest

from app.routing import IntentDecision, resolve_intent
from app.routing.resolve import _parser_source


class TestParserSource:
    def test_rules_mode(self, monkeypatch) -> None:
        monkeypatch.setenv("NLP_CHAT_MODE", "rules")
        assert _parser_source("wyślij fakturę") == "rules"


class TestResolveIntent:
    @pytest.mark.asyncio
    async def test_invoice_rules_path(self) -> None:
        decision, nlp = await resolve_intent("Wyślij fakturę na 1500 PLN do a@b.pl")
        assert nlp is not None
        assert decision.authorized is True
        assert decision.action == "send_invoice"
        assert decision.source in ("rules", "llm", "action_aliases")
        assert decision.to_dict()["intent"] == "send_invoice"

    @pytest.mark.asyncio
    async def test_unknown_intent(self) -> None:
        decision, nlp = await resolve_intent("zrób coś zupełnie losowego xyz123")
        assert nlp is not None
        assert decision.intent == "unknown"
        assert decision.authorized is True

    @pytest.mark.asyncio
    async def test_native_file_list_route(self) -> None:
        decision, nlp = await resolve_intent("lista plikow usera", connector="mullm")
        assert nlp is not None
        assert decision.source == "orientation"
        assert decision.action == "mullm_shell_task"

    @pytest.mark.asyncio
    async def test_decision_serializable(self) -> None:
        decision, _ = await resolve_intent("Wyślij fakturę")
        payload = decision.to_dict()
        assert "source" in payload
        assert "reason_codes" in payload
        assert "authorized" in payload


class TestOrchestratorRoutingField:
    @pytest.mark.asyncio
    async def test_start_conversation_includes_routing(self, monkeypatch) -> None:
        import app.orchestrator as orch_mod
        from app.orchestrator import start_conversation
        from app.store.memory import MemoryConversationStore

        monkeypatch.setattr(orch_mod, "_store", MemoryConversationStore())
        resp = await start_conversation("Wyślij fakturę na 100 PLN do x@y.pl")
        assert resp.routing is not None
        assert resp.routing.get("action") == "send_invoice"
        assert resp.routing.get("authorized") is True
