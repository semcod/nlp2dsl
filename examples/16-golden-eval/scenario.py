"""Golden dataset evaluation — metryki per klasa błędu."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.evaluation import (
    default_golden_cases,
    evaluate_golden_case,
    run_golden_evaluation,
)
from nlp2dsl_sdk.preview import ensure_services

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _print_report(report: Any) -> None:
    print(f"\n📊 Golden: pass={report.passed}/{report.total} ({report.pass_rate}%)")
    print("\n   Per focus (klasa błędu):")
    for focus, stats in sorted(report.by_focus.items()):
        print(f"      {focus}: {stats['passed']}/{stats['total']} ({stats['pass_rate']}%)")
    print("\n   Per action:")
    for action, stats in sorted(report.by_action.items()):
        print(f"      {action}: {stats['passed']}/{stats['total']} ({stats['pass_rate']}%)")
    if report.by_outcome:
        print("\n   Outcome classes:")
        for outcome, count in sorted(report.by_outcome.items()):
            if outcome != "success":
                print(f"      {outcome}: {count}")


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Golden dataset evaluation ===\n")

    if not ensure_services(client):
        return {}

    cases = default_golden_cases()
    results: dict[str, dict[str, Any]] = {}

    for case in cases:
        print(f"▶ [{case.id}] focus={case.focus} mode={case.mode}")
        try:
            result = client.workflow_from_text(case.text, execute=False, mode=case.mode)
        except Exception as exc:
            result = {"status": "error", "error": str(exc)}
        results[case.id] = result
        row = evaluate_golden_case(case, result)
        icon = "✅" if row.passed else "❌"
        print(f"   {icon} status={row.actual_status} actions={list(row.actual_actions)}")
        if not row.passed:
            print(f"      outcome={row.outcome_class} missing={list(row.missing)}")

    report = run_golden_evaluation(cases, results)
    _print_report(report)

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"golden_{int(time.time())}.json"
    out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 Raport: {out}")

    return report.to_dict()
