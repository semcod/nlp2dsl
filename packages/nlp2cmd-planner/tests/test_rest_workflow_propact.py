from pact_ir import IntentIR, TargetKind

from nlp2cmd_planner.strategies.rest_workflow import RestWorkflowPlanStrategy
from nlp2cmd_propact import plan_to_propact_markdown


def test_rest_workflow_renders_propact_markdown(monkeypatch):
    monkeypatch.setenv("NLP2CMD_NLP2DSL_WORKFLOW", "1")
    payload = {
        "status": "complete",
        "dsl": {
            "name": "auto_send_invoice",
            "trigger": "manual",
            "steps": [{"action": "send_invoice", "config": {"amount": 1500, "to": "a@b.pl"}}],
        },
    }
    monkeypatch.setattr(
        "nlp2cmd_planner.strategies.rest_workflow.fetch_workflow_from_text",
        lambda query: payload,
    )

    intent = IntentIR(
        query="Wyślij fakturę na 1500 PLN do klient@firma.pl",
        intent="send_invoice",
        domain="workflow",
        target_kind=TargetKind.REST,
        confidence=0.9,
    )
    plan = RestWorkflowPlanStrategy().plan(intent)
    md = plan_to_propact_markdown(plan)
    assert "```propact:rest" in md
    assert "POST /workflow/run" in md
    assert "send_invoice" in md
