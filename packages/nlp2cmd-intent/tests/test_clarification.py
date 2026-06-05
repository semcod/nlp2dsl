import os

import pytest

from nlp2cmd_intent import IntentClarificationRequired, IntentPipeline, ensure_intent_clear
from nlp2cmd_intent.input import analyze_query


def test_ensure_intent_clear_blocks_low_confidence():
    intent = IntentPipeline().run("xyz")
    assert intent.needs_clarification()

    with pytest.raises(IntentClarificationRequired):
        ensure_intent_clear(intent, enforced=True)


def test_ensure_intent_clear_allows_confident_intent():
    intent = IntentPipeline().run("znajdź pliki *.py w src")
    ensure_intent_clear(intent, enforced=True)


def test_analyze_query_enforces_clarification_with_env(monkeypatch):
    monkeypatch.setenv("NLP2CMD_ENFORCE_CLARIFICATION", "1")
    with pytest.raises(IntentClarificationRequired):
        analyze_query("xyz")


def test_analyze_query_allows_ambiguous_without_env(monkeypatch):
    monkeypatch.delenv("NLP2CMD_ENFORCE_CLARIFICATION", raising=False)
    data = analyze_query("xyz")
    assert data["intent_ir"]["intent"] == "unknown"
