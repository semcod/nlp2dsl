from __future__ import annotations

from dsl_validate.issue import ValidationIssue
from nlp2dsl_sdk.workflow import (
    execution_request_from_workflow,
    parse_result_from_nlp,
    plan_result_from_dialog,
    validation_report_from_issues,
)


def test_parse_result_from_nlp_compacts_entities() -> None:
    result = parse_result_from_nlp(
        "Wyślij fakturę",
        "rules",
        {
            "intent": {"intent": "send_invoice", "confidence": 0.91},
            "entities": {"amount": 1500, "to": None},
            "missing": ["to"],
        },
    )

    assert result.stage == "parse"
    assert result.status == "complete"
    assert result.intent == "send_invoice"
    assert result.entities == {"amount": 1500}
    assert result.missing == ["to"]


def test_plan_result_from_dialog_exposes_clarification() -> None:
    plan = plan_result_from_dialog(
        {
            "status": "incomplete",
            "missing_fields": ["send_invoice.to"],
            "prompt_user": "Podaj adres e-mail odbiorcy",
        }
    )

    assert plan.status == "incomplete"
    assert plan.clarification is not None
    assert plan.clarification.status == "incomplete"
    assert plan.clarification.missing_fields == ["send_invoice.to"]


def test_validation_report_and_execution_request_block_invalid_workflow() -> None:
    report = validation_report_from_issues(
        [
            ValidationIssue(
                code="workflow.missing_action",
                field_name="steps.0.action",
                kind="missing",
            )
        ]
    )
    request = execution_request_from_workflow(
        {"name": "broken", "steps": [{"config": {}}]},
        execute=True,
        validation=report,
    )

    assert report.status == "validation_failed"
    assert report.missing_fields == ["steps.0.action"]
    assert request.status == "blocked"
