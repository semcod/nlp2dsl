from __future__ import annotations

import json

import pytest
from pact_ir import IntentIR, TargetKind

from nlp2cmd_planner.router import PlanRouter, UnsupportedIntentError
from nlp2cmd_planner.strategies.rest_workflow import RestWorkflowPlanStrategy


def _intent(**kwargs) -> IntentIR:
    defaults = {
        "query": "Wyślij fakturę na 1500 PLN do klient@firma.pl",
        "intent": "send_invoice",
        "domain": "workflow",
        "target_kind": TargetKind.REST,
        "confidence": 0.9,
    }
    defaults.update(kwargs)
    return IntentIR(**defaults)


def test_supports_when_workflow_enabled(monkeypatch):
    monkeypatch.setenv("NLP2CMD_NLP2DSL_WORKFLOW", "1")
    strategy = RestWorkflowPlanStrategy()
    assert strategy.supports(_intent()) is True
    assert strategy.supports(_intent(intent="find", domain="shell", target_kind=TargetKind.SHELL)) is False


def test_supports_disabled_without_env(monkeypatch):
    monkeypatch.delenv("NLP2CMD_NLP2DSL_WORKFLOW", raising=False)
    strategy = RestWorkflowPlanStrategy()
    assert strategy.supports(_intent()) is False


def test_plan_builds_rest_workflow_step(monkeypatch):
    monkeypatch.setenv("NLP2CMD_NLP2DSL_WORKFLOW", "1")

    payload = {
        "status": "complete",
        "dsl": {
            "name": "auto_send_invoice",
            "trigger": "manual",
            "steps": [{"action": "send_invoice", "config": {"amount": 1500, "to": "a@b.pl"}}],
        },
    }

    def fake_fetch(query: str):
        assert query
        return payload

    monkeypatch.setattr(
        "nlp2cmd_planner.strategies.rest_workflow.fetch_workflow_from_text",
        fake_fetch,
    )

    plan = RestWorkflowPlanStrategy().plan(_intent())
    assert plan.source == "rest_workflow"
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.target_kind == TargetKind.REST
    assert step.params["method"] == "POST"
    assert step.params["endpoint"] == "/workflow/run"
    assert step.params["body"]["name"] == "auto_send_invoice"
    assert step.metadata["workflow_actions"] == ["send_invoice"]


def test_plan_raises_on_incomplete_workflow(monkeypatch):
    monkeypatch.setenv("NLP2CMD_NLP2DSL_WORKFLOW", "1")
    monkeypatch.setattr(
        "nlp2cmd_planner.strategies.rest_workflow.fetch_workflow_from_text",
        lambda query: {"status": "incomplete", "missing_fields": ["send_invoice.to"]},
    )
    with pytest.raises(UnsupportedIntentError):
        RestWorkflowPlanStrategy().plan(_intent())


def test_router_prefers_shell_over_rest(monkeypatch):
    monkeypatch.setenv("NLP2CMD_NLP2DSL_WORKFLOW", "1")
    router = PlanRouter()
    intent = IntentIR(
        query="znajdź pliki *.py w src",
        intent="find",
        domain="shell",
        target_kind=TargetKind.SHELL,
        confidence=0.95,
    )
    strategy = router.select(intent)
    assert strategy.name == "rule_shell"
