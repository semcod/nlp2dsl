"""Metrics and reporting for golden dataset evaluation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from .golden import (
    ErrorClassFocus,
    GoldenCase,
    extract_actions,
    extract_missing,
)

OutcomeClass = Literal[
    "success",
    "entity_extraction",
    "dsl_mapping",
    "unnecessary_clarification",
    "unsafe_execution_block",
    "attachment_validation",
    "status_mismatch",
    "unknown",
]


@dataclass
class GoldenRow:
    case_id: str
    focus: ErrorClassFocus
    category: str
    mode: str
    expected_status: str
    actual_status: str
    expected_actions: tuple[str, ...]
    actual_actions: tuple[str, ...]
    passed: bool
    outcome_class: OutcomeClass
    missing: tuple[str, ...] = ()
    notes: str = ""


@dataclass
class GoldenReport:
    total: int = 0
    passed: int = 0
    pass_rate: float = 0.0
    by_focus: dict[str, dict[str, int | float]] = field(default_factory=dict)
    by_action: dict[str, dict[str, int | float]] = field(default_factory=dict)
    by_outcome: dict[str, int] = field(default_factory=dict)
    rows: list[GoldenRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "by_focus": self.by_focus,
            "by_action": self.by_action,
            "by_outcome": self.by_outcome,
            "rows": [
                {
                    "case_id": row.case_id,
                    "focus": row.focus,
                    "category": row.category,
                    "mode": row.mode,
                    "expected_status": row.expected_status,
                    "actual_status": row.actual_status,
                    "expected_actions": list(row.expected_actions),
                    "actual_actions": list(row.actual_actions),
                    "passed": row.passed,
                    "outcome_class": row.outcome_class,
                    "missing": list(row.missing),
                    "notes": row.notes,
                }
                for row in self.rows
            ],
        }


def _actions_match(expected: tuple[str, ...], actual: list[str]) -> bool:
    if not expected:
        return True
    return all(any(exp in action for action in actual) for exp in expected)


def _missing_match(expected: tuple[str, ...], actual: list[str]) -> bool:
    if not expected:
        return True
    return all(any(exp in item for item in actual) for exp in expected)


def _has_attachment_signal(result: dict[str, Any], missing: list[str]) -> bool:
    blob = str(result).lower()
    if "attachment" in blob:
        return True
    return any("attachment" in item.lower() for item in missing)


def classify_outcome(case: GoldenCase, result: dict[str, Any]) -> OutcomeClass:
    """Map a failed case to a regression error class."""
    status = str(result.get("status") or "error")
    actions = extract_actions(result)
    missing = extract_missing(result)

    if status == case.expected_status and _actions_match(case.expected_actions, actions):
        if case.expected_status == "incomplete" and not _missing_match(case.expected_missing, missing):
            return "entity_extraction"
        return "success"

    if case.focus == "attachment_validation" or _has_attachment_signal(result, missing):
        return "attachment_validation"

    if case.expected_status in {"validation_failed", "incomplete"} and status == "executed":
        return "unsafe_execution_block"

    if case.expected_status == "complete" and status == "validation_failed":
        return "unsafe_execution_block"

    if case.expected_status == "complete" and status == "incomplete":
        if case.focus == "unnecessary_clarification":
            return "unnecessary_clarification"
        return "entity_extraction"

    if case.expected_status == "incomplete" and status == "complete":
        return "unnecessary_clarification"

    if not _actions_match(case.expected_actions, actions):
        return "dsl_mapping"

    if status != case.expected_status:
        return "status_mismatch"

    return "unknown"


def evaluate_golden_case(case: GoldenCase, result: dict[str, Any]) -> GoldenRow:
    """Evaluate one golden case against a lifecycle/from-text result."""
    status = str(result.get("status") or "error")
    actions = tuple(extract_actions(result))
    missing = tuple(extract_missing(result))
    outcome = classify_outcome(case, result)
    passed = outcome == "success"

    return GoldenRow(
        case_id=case.id,
        focus=case.focus,
        category=case.category,
        mode=case.mode,
        expected_status=case.expected_status,
        actual_status=status,
        expected_actions=case.expected_actions,
        actual_actions=actions,
        passed=passed,
        outcome_class=outcome,
        missing=missing,
        notes=case.notes,
    )


def _bucket_stats(rows: list[GoldenRow], key_fn: Callable[[GoldenRow], str]) -> dict[str, dict[str, int | float]]:
    totals: dict[str, int] = defaultdict(int)
    passed: dict[str, int] = defaultdict(int)
    for row in rows:
        key = key_fn(row)
        totals[key] += 1
        if row.passed:
            passed[key] += 1
    return {
        key: {
            "total": totals[key],
            "passed": passed[key],
            "pass_rate": round(100 * passed[key] / totals[key], 1) if totals[key] else 0.0,
        }
        for key in sorted(totals)
    }


def build_golden_report(rows: list[GoldenRow]) -> GoldenReport:
    total = len(rows)
    passed = sum(1 for row in rows if row.passed)
    by_outcome: dict[str, int] = defaultdict(int)
    for row in rows:
        by_outcome[row.outcome_class] += 1

    return GoldenReport(
        total=total,
        passed=passed,
        pass_rate=round(100 * passed / total, 1) if total else 0.0,
        by_focus=_bucket_stats(rows, lambda row: row.focus),
        by_action=_bucket_stats(rows, lambda row: primary_action_from_row(row)),
        by_outcome=dict(by_outcome),
        rows=rows,
    )


def primary_action_from_row(row: GoldenRow) -> str:
    if row.expected_actions:
        return row.expected_actions[0]
    return row.category


def run_golden_evaluation(
    cases: tuple[GoldenCase, ...],
    results: dict[str, dict[str, Any]],
) -> GoldenReport:
    """Evaluate pre-fetched results keyed by case id."""
    rows = [evaluate_golden_case(case, results.get(case.id, {"status": "error"})) for case in cases]
    return build_golden_report(rows)
