"""DOQL render — write DoqlTaskContext to environment.doql.less."""

from __future__ import annotations

from pathlib import Path

from .context_blocks import (
    render_context_access,
    render_context_artifacts,
    render_context_capabilities,
    render_context_commands,
    render_context_conversation,
    render_context_data,
    render_context_environment,
    render_context_header,
    render_context_paths,
    render_context_process,
    render_context_process_access,
    render_context_resources,
    render_context_runtimes,
    render_context_workflow_history,
)
from .models import DoqlTaskContext


def render_doql_context(ctx: DoqlTaskContext) -> str:
    lines: list[str] = []
    lines.extend(render_context_header(ctx))
    lines.extend(render_context_environment(ctx))
    lines.extend(render_context_data(ctx))
    lines.extend(render_context_artifacts(ctx))
    lines.extend(render_context_commands(ctx))
    lines.extend(render_context_resources(ctx))
    lines.extend(render_context_access(ctx))
    lines.extend(render_context_runtimes(ctx))
    lines.extend(render_context_capabilities(ctx))
    lines.extend(render_context_workflow_history(ctx))
    lines.extend(render_context_process(ctx))
    lines.extend(render_context_process_access(ctx))
    lines.extend(render_context_paths(ctx))
    lines.extend(render_context_conversation(ctx))
    return "\n".join(lines)


def write_doql_context(path: Path | str, ctx: DoqlTaskContext) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_doql_context(ctx), encoding="utf-8")
    return path
