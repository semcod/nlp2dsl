#!/usr/bin/env python3
"""Run a conversation.scenario.yaml against live nlp2dsl (Docker) and write trace artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from _conversation_scenario import (
    check_expect,
    finalize_trace,
    load_yaml,
    prepare_doql_context,
    run_turn,
    run_validation,
    turn_loop_action,
    wait_health,
)

ROOT = Path(__file__).resolve().parents[1]


def _setup_scenario(
    scenario_path: Path,
    base_url: str,
    wait_health_flag: bool,
) -> dict[str, Any]:
    scenario = load_yaml(scenario_path)
    example_dir = scenario_path.parent.parent
    os.environ.setdefault("NLP2DSL_EXAMPLE_DIR", str(example_dir))
    prepare_doql_context(scenario_path, scenario)
    if wait_health_flag and not wait_health(base_url):
        raise RuntimeError(f"nlp2dsl not healthy at {base_url}")
    return scenario


def _run_turns(
    flow: Any,
    scenario: dict[str, Any],
) -> list[str]:
    turn_errors: list[str] = []

    def _process_single_turn(idx: int, turn: dict[str, Any]) -> str | None:
        action = turn_loop_action(flow, turn, idx=idx)
        if action in ("continue", "break"):
            return action
        text = str(turn.get("text", "")).strip()
        if not text:
            turn_errors.append(f"turn {idx}: empty text")
            return None
        response = run_turn(flow, turn, idx=idx)
        expect = turn.get("expect") or {}
        if expect:
            ok, msg = check_expect(response, expect)
            if not ok:
                turn_errors.append(f"turn {idx}: {msg}")
        return None

    for idx, turn in enumerate(scenario.get("turns") or [], start=1):
        action = _process_single_turn(idx, turn)
        if action == "break":
            break
    return turn_errors


def _write_artifacts(
    trace: dict[str, Any],
    out_root: Path,
    scenario: dict[str, Any],
) -> None:
    from testql_conversations.artifacts import write_conversation_artifacts

    write_conversation_artifacts(out_root, trace, scenario_name=scenario.get("name", "scenario"))
    if scenario.get("record_llm_routing"):
        src = out_root / "conversation.trace.json"
        dst = out_root / "conversation.llm.trace.json"
        if src.is_file():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def run_scenario(
    scenario_path: Path,
    *,
    base_url: str,
    artifact_root: Path | None = None,
    wait_health_flag: bool = True,
) -> dict:
    from nlp2dsl_sdk.client import ConversationFlow, NLP2DSLClient

    scenario = _setup_scenario(scenario_path, base_url, wait_health_flag)
    flow = ConversationFlow(NLP2DSLClient(backend_url=base_url))
    turn_errors = _run_turns(flow, scenario)

    validations = [
        run_validation(v, flow._last_response)
        for v in scenario.get("validations") or []
        if isinstance(v, dict)
    ]
    trace = finalize_trace(
        flow,
        scenario_path=scenario_path,
        scenario=scenario,
        turn_errors=turn_errors,
        validations=validations,
    )

    out_root = artifact_root or scenario_path.parent
    _write_artifacts(trace, out_root, scenario)
    return trace


def _print_trace(trace: dict[str, Any], scenario_path: Path, *, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(trace, indent=2, ensure_ascii=False))
        return
    status = "PASSED" if trace.get("passed") else "FAILED"
    print(f"{status}: {scenario_path} — conversation_id={trace.get('conversation_id')}")
    for err in trace.get("errors") or []:
        print(f"  - {err}", file=sys.stderr)
    for v in trace.get("validations") or []:
        mark = "ok" if v.get("passed") else "FAIL"
        print(f"  [{mark}] {v.get('id')}: {v.get('summary')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path, help="Path to conversation.scenario.yaml")
    parser.add_argument("--base-url", default="http://localhost:8010")
    parser.add_argument("--no-wait", action="store_true", help="Skip health wait")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    scenario_path = args.scenario.resolve()
    if not scenario_path.is_file():
        print(f"Missing scenario: {scenario_path}", file=sys.stderr)
        return 2

    try:
        trace = run_scenario(
            scenario_path,
            base_url=args.base_url,
            wait_health_flag=not args.no_wait,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    _print_trace(trace, scenario_path, json_mode=args.json)
    return 0 if trace.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
