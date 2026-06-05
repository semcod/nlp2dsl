"""CLI: show NL query structure as IR (no execution)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import yaml

from nlp2cmd_intent.input import analyze_query


def _serialize(data: dict[str, Any], fmt: str) -> str:
    if fmt == "yaml":
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    return json.dumps(data, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    from nlp2dsl_show.encoding import configure_utf8

    configure_utf8()

    parser = argparse.ArgumentParser(
        prog="nlp2dsl",
        description="Show NL query structure (IntentIR). Does not execute commands.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Render IntentIR for a user query")
    show.add_argument("query", help="Natural language query")
    show.add_argument(
        "--plan",
        action="store_true",
        help="Also include ExecutionPlanIR (structure only, no Propact/run)",
    )
    show.add_argument(
        "--format",
        choices=("json", "yaml"),
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args(argv)
    if args.command != "show":
        parser.error(f"unknown command {args.command!r}")

    try:
        payload = analyze_query(args.query, include_plan=args.plan)
    except Exception as exc:
        from nlp2cmd_intent import IntentClarificationRequired

        if isinstance(exc, IntentClarificationRequired):
            print(f"error: {exc}", file=sys.stderr)
            return 2
        raise

    if args.plan:
        payload = _attach_contract_check(payload)

    print(_serialize(payload, args.format))
    if args.plan and payload.get("contract_check", {}).get("passed") is False:
        return 1
    return 0


def _attach_contract_check(payload: dict[str, Any]) -> dict[str, Any]:
    """Add Intract contract_check when gate is enabled and plan is present."""
    plan_data = payload.get("execution_plan_ir")
    intent_data = payload.get("intent_ir")
    if not plan_data or not intent_data:
        return payload

    try:
        from nlp2cmd.intract.plan_gate import validate_plan_contracts_if_enabled
        from pact_ir import ExecutionPlanIR, IntentIR
    except ImportError:
        return payload

    intent = IntentIR.model_validate(intent_data)
    plan = ExecutionPlanIR.model_validate(plan_data)
    contract_check = validate_plan_contracts_if_enabled(plan, intent)
    if contract_check is not None:
        payload["contract_check"] = contract_check
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
