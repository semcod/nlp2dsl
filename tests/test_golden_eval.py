"""Tests for golden dataset evaluation."""

from __future__ import annotations

from nlp2dsl_sdk.evaluation.golden import GoldenCase, default_golden_cases, load_golden_cases
from nlp2dsl_sdk.evaluation.metrics import classify_outcome, evaluate_golden_case, run_golden_evaluation


def test_load_bundled_golden_cases() -> None:
    cases = default_golden_cases()
    assert len(cases) >= 10
    focuses = {case.focus for case in cases}
    assert "dsl_mapping" in focuses
    assert "entity_extraction" in focuses


def test_evaluate_golden_case_success() -> None:
    case = GoldenCase(
        id="t1",
        text="Wyślij fakturę na 500 PLN do a@b.pl",
        focus="entity_extraction",
        expected_status="complete",
        expected_actions=("send_invoice",),
    )
    row = evaluate_golden_case(
        case,
        {
            "status": "complete",
            "dsl": {"steps": [{"action": "send_invoice", "config": {}}]},
        },
    )
    assert row.passed is True
    assert row.outcome_class == "success"


def test_classify_dsl_mapping_failure() -> None:
    case = GoldenCase(
        id="t2",
        text="composite",
        focus="dsl_mapping",
        expected_status="complete",
        expected_actions=("send_invoice", "notify_slack"),
    )
    outcome = classify_outcome(
        case,
        {
            "status": "complete",
            "dsl": {"steps": [{"action": "send_invoice", "config": {}}]},
        },
    )
    assert outcome == "dsl_mapping"


def test_classify_unnecessary_clarification() -> None:
    case = GoldenCase(
        id="t3",
        text="invoice complete",
        focus="unnecessary_clarification",
        expected_status="complete",
        expected_actions=("send_invoice",),
    )
    outcome = classify_outcome(
        case,
        {"status": "incomplete", "missing_fields": ["send_invoice.to"]},
    )
    assert outcome == "unnecessary_clarification"


def test_classify_unsafe_execution_block() -> None:
    case = GoldenCase(
        id="t4",
        text="broken",
        focus="unsafe_execution_block",
        expected_status="validation_failed",
        expected_actions=(),
    )
    outcome = classify_outcome(case, {"status": "executed", "dsl": {"steps": []}})
    assert outcome == "unsafe_execution_block"


def test_run_golden_evaluation_report() -> None:
    cases = load_golden_cases()
    assert cases
    first = cases[0]
    report = run_golden_evaluation(
        (first,),
        {
            first.id: {
                "status": first.expected_status,
                "dsl": {
                    "steps": [{"action": action, "config": {}} for action in first.expected_actions]
                },
            }
        },
    )
    assert report.total == 1
    assert report.passed == 1
    assert first.focus in report.by_focus
