"""Render DoqlTaskContext blocks → DOQL lines."""

from __future__ import annotations

from ..system_map_render.helpers import bool_lit, data_value_line, esc_str, join_csv
from .models import DoqlTaskContext


def render_context_header(ctx: DoqlTaskContext) -> list[str]:
    return [
        f"// DOQL system map — {ctx.example_name}",
        "// role: schema of available services, commands, resources, artifacts, access",
        f"// generated: {ctx.generated_at}",
        "",
    ]


def render_context_environment(ctx: DoqlTaskContext) -> list[str]:
    lines = [f'environment[name="{ctx.example_name}"] {{']
    for key in sorted(ctx.environment):
        if key == "generated_at":
            continue
        lines.append(f'  {key}: "{esc_str(str(ctx.environment[key]))}";')
    lines.extend(["}", ""])
    return lines


def render_context_data(ctx: DoqlTaskContext) -> list[str]:
    lines = ["data {"]
    for key in sorted(ctx.data):
        lines.append(data_value_line(key, ctx.data[key]))
    lines.extend(["}", ""])
    return lines


def render_context_artifacts(ctx: DoqlTaskContext) -> list[str]:
    lines: list[str] = []
    for idx, art in enumerate(ctx.artifacts):
        lines.append(f"artifacts[{idx}] {{")
        lines.append(f'  path: "{art.path}";')
        lines.append(f'  kind: "{art.kind}";')
        for k, v in sorted(art.values.items()):
            if isinstance(v, str):
                lines.append(f'  {k}: "{v}";')
            else:
                lines.append(f"  {k}: {v};")
        lines.extend(["}", ""])
    return lines


def render_context_commands(ctx: DoqlTaskContext) -> list[str]:
    lines: list[str] = []
    for idx, cmd in enumerate(ctx.commands):
        lines.append(f"commands[{idx}] {{")
        lines.append(f'  name: "{cmd.name}";')
        if cmd.description:
            lines.append(f'  description: "{esc_str(cmd.description)}";')
        if cmd.required:
            lines.append(f'  required: "{join_csv(cmd.required)}";')
        if cmd.optional:
            lines.append(f'  optional: "{join_csv(cmd.optional)}";')
        if cmd.runtime:
            lines.append(f'  runtime: "{cmd.runtime}";')
        lines.append(f'  transport: "{cmd.transport}";')
        lines.append(f'  endpoint: "{cmd.endpoint}";')
        lines.extend(["}", ""])
    return lines


def render_context_resources(ctx: DoqlTaskContext) -> list[str]:
    lines: list[str] = []
    for idx, res in enumerate(ctx.resources):
        lines.append(f"resources[{idx}] {{")
        lines.append(f'  id: "{res.id}";')
        if res.title:
            lines.append(f'  title: "{esc_str(res.title)}";')
        if res.connector:
            lines.append(f'  connector: "{res.connector}";')
        if res.uri_patterns:
            lines.append(f'  uri_patterns: "{join_csv(res.uri_patterns)}";')
        lines.extend(["}", ""])
    return lines


def render_context_access(ctx: DoqlTaskContext) -> list[str]:
    lines: list[str] = []
    for idx, grant in enumerate(ctx.access):
        lines.append(f"access[{idx}] {{")
        lines.append(f'  agent: "{grant.agent}";')
        if grant.resource_area:
            lines.append(f'  resource_area: "{grant.resource_area}";')
        if grant.actions:
            lines.append(f'  actions: "{join_csv(grant.actions)}";')
        lines.append(f'  effect: "{grant.effect}";')
        lines.extend(["}", ""])
    return lines


def render_context_runtimes(ctx: DoqlTaskContext) -> list[str]:
    lines: list[str] = []
    for idx, rt in enumerate(ctx.runtimes):
        lines.append(f"runtimes[{idx}] {{")
        lines.append(f'  id: "{rt.id}";')
        if rt.kind:
            lines.append(f'  kind: "{rt.kind}";')
        if rt.url:
            lines.append(f'  url: "{rt.url}";')
        if rt.uri:
            lines.append(f'  uri: "{rt.uri}";')
        if rt.health:
            lines.append(f'  health: "{rt.health}";')
        if rt.docker_profile:
            lines.append(f'  docker_profile: "{rt.docker_profile}";')
        if rt.model:
            lines.append(f'  model: "{rt.model}";')
        if rt.roles:
            lines.append(f'  roles: "{join_csv(rt.roles)}";')
        if rt.status:
            lines.append(f'  status: "{rt.status}";')
        lines.extend(["}", ""])
    return lines


def render_context_capabilities(ctx: DoqlTaskContext) -> list[str]:
    if not ctx.capabilities:
        return []
    return [
        "capabilities {",
        f'  actions: "{join_csv(ctx.capabilities)}";',
        "}",
    ]


def render_context_workflow_history(ctx: DoqlTaskContext) -> list[str]:
    if not ctx.workflow_history:
        return []
    lines = ["", "workflow_history {"]
    for key in sorted(ctx.workflow_history):
        val = ctx.workflow_history[key]
        if isinstance(val, list):
            lines.append(f'  {key}: "{join_csv([str(v) for v in val])}";')
        elif isinstance(val, str):
            lines.append(f'  {key}: "{val}";')
        else:
            lines.append(f"  {key}: {val};")
    lines.append("}")
    return lines


def render_context_process(ctx: DoqlTaskContext) -> list[str]:
    proc = ctx.process
    if proc.mode == "balanced" and proc.nlp_parser == "auto" and proc.autonomous_max_rounds == 8:
        if not (
            proc.nlp_enrich_missing
            or proc.llm_temperature is not None
            or not proc.autonomous_enabled
            or proc.ask_user != "when_exhausted"
            or proc.intract_gate
            or proc.intract_enforce_clarification
            or proc.llm_reasoning != "shallow"
        ):
            return []

    lines = ["", "process {"]
    lines.append(f'  mode: "{proc.mode}";')
    lines.append(f'  nlp_parser: "{proc.nlp_parser}";')
    lines.append(f"  nlp_confidence_min: {proc.nlp_confidence_min};")
    if proc.nlp_enrich_missing:
        lines.append("  nlp_enrich_missing: true;")
    lines.append(f'  llm_reasoning: "{proc.llm_reasoning}";')
    if proc.llm_temperature is not None:
        lines.append(f"  llm_temperature: {proc.llm_temperature};")
    if not proc.autonomous_enabled:
        lines.append("  autonomous: false;")
    if proc.autonomous_max_rounds != 8:
        lines.append(f"  autonomous_max_rounds: {proc.autonomous_max_rounds};")
    if proc.ask_user != "when_exhausted":
        lines.append(f'  ask_user: "{proc.ask_user}";')
    if proc.intract_gate:
        lines.append("  intract_gate: true;")
    if proc.intract_enforce_clarification:
        lines.append("  intract_enforce_clarification: true;")
    lines.append("}")
    return lines


def render_context_process_access(ctx: DoqlTaskContext) -> list[str]:
    proc = ctx.process
    if not (proc.agent or proc.allow_resource_areas or proc.deny_resource_areas):
        return []
    lines = ["", "process_access {"]
    if proc.agent:
        lines.append(f'  agent: "{proc.agent}";')
    if proc.allow_resource_areas:
        lines.append(f'  allow_areas: "{join_csv(proc.allow_resource_areas)}";')
    if proc.deny_resource_areas:
        lines.append(f'  deny_areas: "{join_csv(proc.deny_resource_areas)}";')
    lines.append("}")
    return lines


def render_context_paths(ctx: DoqlTaskContext) -> list[str]:
    proc = ctx.process
    if not (proc.paths_read or proc.paths_write):
        return []
    lines = ["", "paths {"]
    if proc.paths_read:
        lines.append(f'  read: "{join_csv(proc.paths_read)}";')
    if proc.paths_write:
        lines.append(f'  write: "{join_csv(proc.paths_write)}";')
    lines.append("}")
    return lines


def render_context_conversation(ctx: DoqlTaskContext) -> list[str]:
    return [
        "",
        "conversation {",
        f"  autofill: {bool_lit(ctx.autofill)};",
        f"  sync_auto_execute: {bool_lit(ctx.sync_auto_execute)};",
        *(
            ["  attachment_required: true;"]
            if ctx.attachment_required
            else []
        ),
        f"  generate_invoice_if_missing: {bool_lit(ctx.generate_invoice_if_missing)};",
        *(
            ["  strict_pdf: true;"]
            if ctx.strict_pdf
            else []
        ),
        "}",
        "",
    ]
