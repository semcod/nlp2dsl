"""Write command handlers — append events after success."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsl2nlp2dsl.result import DslResult
from dsl2nlp2dsl.handlers import query


def _load_workflow(cmd: dict[str, Any]) -> dict[str, Any] | None:
    if wf := cmd.get("workflow"):
        return dict(wf)
    if path := cmd.get("workflow_file"):
        text = Path(path).expanduser().read_text(encoding="utf-8")
        return json.loads(text) if path.endswith(".json") else __import__("yaml").safe_load(text)
    return None


def handle_execute(cmd: dict[str, Any], *, line: str) -> DslResult:
    from nlp2dsl_sdk.client import NLP2DSLClient

    dry_run = bool(cmd.get("dry_run"))
    mode = cmd.get("mode", "auto")
    try:
        with NLP2DSLClient.from_env() as client:
            if text := cmd.get("text"):
                data = client.workflow_from_text(text, execute=not dry_run, mode=mode, simulate=dry_run)
            else:
                workflow = _load_workflow(cmd)
                if workflow is None:
                    return DslResult(ok=False, command=line, action="execute", error="EXECUTE requires text or workflow_file")
                if dry_run:
                    data = client.workflow_simulate(workflow=workflow, mode=mode)
                else:
                    data = client.workflow_execute(workflow, dry_run=False)
        ok = data.get("status") not in {"failed", "validation_failed", "blocked"}
        return DslResult(ok=ok, command=line, action="execute", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="execute", error=str(exc))


def handle_simulate(cmd: dict[str, Any], *, line: str) -> DslResult:
    cmd = dict(cmd)
    cmd["dry_run"] = True
    result = handle_execute(cmd, line=line)
    result.action = "simulate"
    return result


def handle_generate(cmd: dict[str, Any], *, line: str) -> DslResult:
    from nlp2dsl_sdk.client import NLP2DSLClient

    text = cmd.get("text", "")
    mode = cmd.get("mode", "auto")
    try:
        with NLP2DSLClient.from_env() as client:
            data = client.workflow_from_text(text, execute=False, mode=mode)
        out = cmd.get("out")
        if out and data.get("workflow"):
            Path(out).expanduser().write_text(json.dumps(data["workflow"], ensure_ascii=False, indent=2), encoding="utf-8")
            data["output_path"] = str(Path(out).resolve())
        return DslResult(ok=True, command=line, action="generate", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="generate", error=str(exc))


def handle_chat(cmd: dict[str, Any], *, line: str) -> DslResult:
    from nlp2dsl_sdk.client import NLP2DSLClient

    text = cmd.get("text", "")
    try:
        with NLP2DSLClient.from_env() as client:
            data = client.chat_start(text)
        return DslResult(ok=True, command=line, action="chat", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="chat", error=str(exc))


def handle_draft(cmd: dict[str, Any], *, line: str) -> DslResult:
    from dsl_contracts.draft import load_draft, save_draft, validate_draft, ContractDraft

    name = cmd.get("name", "")
    draft_file = cmd.get("draft_file")
    status = cmd.get("status")
    try:
        if draft_file:
            draft = load_draft(draft_file)
        elif name:
            from dsl_contracts.draft import draft_path, load_drafts

            matches = [d for d in load_drafts() if d.name == name]
            if not matches:
                return DslResult(ok=False, command=line, action="draft", error=f"draft not found: {name}")
            draft = matches[0]
        else:
            return DslResult(ok=False, command=line, action="draft", error="DRAFT requires name or FILE")

        if status:
            draft.status = status  # type: ignore[assignment]
            path = save_draft(draft, draft_file)
            data = {"draft": draft.to_yaml_dict(), "path": str(path)}
            return DslResult(ok=True, command=line, action="draft", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)

        issues = validate_draft(draft)
        data = {"draft": draft.to_yaml_dict(), "issues": [i.model_dump() for i in issues]}
        return DslResult(
            ok=not issues,
            command=line,
            action="draft",
            output=json.dumps(data, ensure_ascii=False, indent=2),
            data=data,
            error=None if not issues else "draft validation failed",
        )
    except Exception as exc:
        return DslResult(ok=False, command=line, action="draft", error=str(exc))


def handle_observe(cmd: dict[str, Any], *, line: str) -> DslResult:
    from env2llm.layout import ensure_layout, write_registry
    from env2llm.generate import generate_system_map
    from env2llm.render.doql import render_system_map_doql

    target = Path(cmd.get("target", ".")).expanduser().resolve()
    try:
        system_map = generate_system_map(target)
        artifact_root = target / ".nlp2dsl"
        ensure_layout(artifact_root)
        path = write_registry(artifact_root, render_system_map_doql(system_map))
        data = {"target": str(target), "registry": str(path)}
        return DslResult(ok=True, command=line, action="observe", output=json.dumps(data, ensure_ascii=False, indent=2), data=data)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="observe", error=str(exc))


def handle_compose(cmd: dict[str, Any], *, line: str) -> DslResult:
    from env2llm.generate import generate_system_map
    from env2llm.runtimes import load_example_profile
    from nlp2dsl_stack.compose import generate_stack_compose

    profile_id = cmd.get("profile", "default")
    target = Path(cmd.get("target", ".")).expanduser().resolve()
    try:
        profile = load_example_profile(profile_id, target.parent)
        ir = generate_system_map(target)
        gen = generate_stack_compose(ir, example_dir=target, example_id=profile_id, profile=profile)
        result = {
            "profile": profile_id,
            "stack_compose": str(gen.stack_compose),
            "manifest": str(gen.manifest),
            "crontab": str(gen.crontab),
        }
        out = cmd.get("out")
        if out:
            Path(out).expanduser().write_text(gen.stack_compose.read_text(encoding="utf-8"), encoding="utf-8")
            result["output_path"] = str(Path(out).resolve())
        return DslResult(ok=True, command=line, action="compose", output=json.dumps(result, ensure_ascii=False, indent=2), data=result)
    except Exception as exc:
        return DslResult(ok=False, command=line, action="compose", error=str(exc))
