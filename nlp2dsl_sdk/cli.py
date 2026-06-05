"""nlp2dsl CLI: analyze NL queries (IntentIR + optional ExecutionPlanIR)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _analyze(query: str, *, include_plan: bool = False) -> dict[str, Any] | None:
    """Analyze query via nlp2cmd_intent (best-effort, optional import)."""
    try:
        from nlp2cmd_intent.input import analyze_query
        return analyze_query(query, include_plan=include_plan)
    except ImportError:
        return None


def _display(result: dict[str, Any], *, plan: bool = False) -> None:
    """Pretty-print analysis result."""
    intent_ir = result.get("intent_ir") or {}
    execution_plan_ir = result.get("execution_plan_ir")
    plan_error = result.get("plan_error")

    print(f"Analiza tekstu: {result.get('query', '')!r}")
    print()

    # Intent
    print(f"intent={intent_ir.get('intent', 'unknown')} "
          f"domain={intent_ir.get('domain', '?')} "
          f"target={intent_ir.get('target_kind', 'unknown')} "
          f"confidence={float(intent_ir.get('confidence', 0.0)):.2f}")

    # Entities
    entities = intent_ir.get("entities")
    if entities:
        print("entities:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

    # Plan
    conf = float(intent_ir.get("confidence", 0.0))
    intent_val = intent_ir.get("intent", "unknown")
    if plan and conf > 0.0 and intent_val != "unknown" and execution_plan_ir:
        print()
        print("ExecutionPlanIR:")
        print(json.dumps(execution_plan_ir, ensure_ascii=False, indent=2))
    elif plan and plan_error:
        print()
        print(f"plan_error: {plan_error}")
    elif plan and (conf < 0.01 or intent_val == "unknown"):
        print()
        print("ExecutionPlanIR: (not available — low confidence)")


def show(query: str, *, plan: bool = False) -> int:
    """Analyze and display query structure."""
    result = _analyze(query, include_plan=plan)
    if result is None:
        print(
            "nlp2cmd_intent not available. Install with:\n"
            "  pip install nlp2cmd-intent",
            file=sys.stderr,
        )
        return 2
    _display(result, plan=plan)
    return 0


def _client():
    from .client import NLP2DSLClient
    return NLP2DSLClient.from_env()


def _health() -> int:
    try:
        c = _client()
        result = c.health()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        c.close()
        return 0
    except Exception as e:
        print(f"❌ Cannot connect: {e}", file=sys.stderr)
        return 1


def _run(query: str, *, execute: bool = False, json_output: bool = False) -> int:
    try:
        c = _client()
        result = c.workflow_from_text(query, execute=execute)
        c.close()
        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        status = result.get("status", "unknown")
        print(f"Status: {status}")

        if status == "incomplete":
            missing = result.get("missing_fields") or []
            if missing:
                print(f"❗ Missing: {', '.join(missing)}")
            prompt = result.get("prompt_user")
            if prompt:
                print(f"🤖 {prompt}")
            return 0

        dsl = result.get("dsl")
        if dsl:
            print(f"Workflow: {dsl.get('name', '?')} ({len(dsl.get('steps', []))} kroków)")
            for i, step in enumerate(dsl.get("steps", []), 1):
                print(f"  {i}. {step.get('action', '')} -> {step.get('config', {})}")

        execution = result.get("execution")
        if execution:
            exec_status = execution.get("status", "?")
            print(f"Execution: {exec_status}")
            for step in execution.get("steps", []):
                step_status = step.get("status", "?")
                icon = "✅" if step_status == "completed" else "❌"
                print(f"  {icon} {step.get('action', '')}: {step_status}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def _actions() -> int:
    try:
        c = _client()
        result = c.workflow_actions()
        c.close()
        print("Available actions:")
        for action in result:
            print(f"  • {action.get('name', '?')}: {action.get('description', '')}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def _chat_start(text: str) -> int:
    try:
        c = _client()
        result = c.chat_start(text)
        c.close()
        conv_id = result.get("conversation_id")
        print(f"Conversation started: {conv_id}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message', '')}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


def _demo(name: str | None, list_demos: bool) -> int:
    from .demos import list_available_demos
    specs = list_available_demos()
    spec_map = {spec.name: spec for spec in specs}
    if list_demos:
        print("Dostępne demo:")
        for spec in specs:
            print(f"- {spec.name}: {spec.description}")
        return 0
    if not name or name not in spec_map:
        print(f"Unknown demo '{name}'. Use --list to inspect available demos.", file=sys.stderr)
        return 2
    spec_map[name].runner()
    return 0


def main(argv: list[str] | None = None) -> int:
    from nlp2dsl_sdk.encoding import configure_utf8

    configure_utf8()

    parser = argparse.ArgumentParser(description="NLP2DSL SDK CLI")
    sub = parser.add_subparsers(dest="command")

    # show
    show_parser = sub.add_parser("show", help="Analyze NL query (IntentIR)")
    show_parser.add_argument("query", help="Natural language query")
    show_parser.add_argument("--plan", action="store_true", help="Include ExecutionPlanIR")

    # run
    run_parser = sub.add_parser("run", help="Run workflow from NL query")
    run_parser.add_argument("query", help="Natural language query")
    run_parser.add_argument("--execute", action="store_true", help="Execute workflow immediately")
    run_parser.add_argument("--json", action="store_true", dest="json_output", help="Output raw JSON")

    # health
    sub.add_parser("health", help="Check backend health")

    # actions
    sub.add_parser("actions", help="List available workflow actions")

    # chat
    chat_parser = sub.add_parser("chat", help="Start a conversation")
    chat_parser.add_argument("text", help="Initial message")

    # demo
    demo_parser = sub.add_parser("demo", help="Run SDK demos")
    demo_parser.add_argument("name", nargs="?", default="invoice", help="Demo name (default: invoice)")
    demo_parser.add_argument("--list", action="store_true", dest="list_demos", help="List available demos")

    args = parser.parse_args(argv)

    if args.command == "show":
        return show(args.query, plan=args.plan)
    if args.command == "run":
        return _run(args.query, execute=args.execute, json_output=args.json_output)
    if args.command == "health":
        return _health()
    if args.command == "actions":
        return _actions()
    if args.command == "chat":
        return _chat_start(args.text)
    if args.command == "demo":
        return _demo(args.name, args.list_demos)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
