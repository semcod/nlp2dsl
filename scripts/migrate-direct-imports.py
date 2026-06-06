#!/usr/bin/env python3
"""One-shot: replace nlp2dsl_sdk shim imports with direct package imports."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KORU = ROOT.parent.parent / "semcod" / "koru"

# Longest prefixes first.
TEXT_REPLACEMENTS = [
    ("from nlp2dsl_sdk.contracts.draft import", "from dsl_contracts.draft import"),
    ("from nlp2dsl_sdk.contracts.registry import", "from dsl_contracts.registry import"),
    ("from nlp2dsl_sdk.contracts import", "from dsl_contracts import"),
    ("from nlp2dsl_sdk.validation.rules.", "from dsl_validate.rules."),
    ("from nlp2dsl_sdk.validation.", "from dsl_validate."),
    ("from nlp2dsl_sdk.validation import", "from dsl_validate import"),
    ("from nlp2dsl_sdk.export.publish import", "from workflow_export.publish import"),
    ("from nlp2dsl_sdk.export.markpact import", "from workflow_export.markpact import"),
    ("from nlp2dsl_sdk.export.pactown import", "from workflow_export.pactown import"),
    ("from nlp2dsl_sdk.export import", "from workflow_export import"),
    ("from nlp2dsl_sdk.conversation_testql import", "from testql_conversations.validate import"),
    ("from nlp2dsl_sdk.conversation_artifacts import", "from testql_conversations.artifacts import"),
    ("from nlp2dsl_sdk.compose_generator import", "from nlp2dsl_stack import"),
    ("from nlp2dsl_sdk.artifacts import", "from nlp2dsl_artifacts import"),
    ("from nlp2dsl_sdk.path_resolve import", "from dsl_validate.path_resolve import"),
    ("from nlp2dsl_sdk.system_map_render import", "from env2llm.render.doql import"),
    ("from nlp2dsl_sdk.system_map_bridge import", "from env2llm.bridge import"),
    ("from nlp2dsl_sdk.system_map_generator import", "from env2llm.generate import"),
    ("from nlp2dsl_sdk.system_map_runtimes import", "from env2llm.runtimes import"),
    ("from nlp2dsl_sdk.system_map_models import", "from env2llm.system_map_models import"),
    ("from nlp2dsl_sdk.system_map_ir import", "from env2llm.ir import"),
    ("from nlp2dsl_sdk.doql_registry import", "from env2llm.registry import"),
    ("from nlp2dsl_sdk.artifact_layout import", "from env2llm.layout import"),
    ("from nlp2dsl_sdk.process_policy import", "from env2llm.policy.process import"),
    ("from nlp2dsl_sdk.invoice_policy import", "from env2llm.policy.invoice import"),
    ("from nlp2dsl_sdk.example_bootstrap import", "from env2llm.bootstrap import"),
    ("from nlp2dsl_sdk.doql.models import", "from env2llm.doql.models import"),
    ("from nlp2dsl_sdk.doql.parse import", "from env2llm.doql.parse import"),
    ("from nlp2dsl_sdk.doql.runtime import", "from env2llm.doql.runtime import"),
    ("from nlp2dsl_sdk.doql.render import", "from env2llm.doql.render import"),
    ("from nlp2dsl_sdk.doql import", "from env2llm.doql import"),
    ("from nlp2dsl_sdk.doql_context import", "from env2llm.doql_context import"),
]

RELATIVE_REPLACEMENTS = [
    ("from .validation.rules.", "from dsl_validate.rules."),
    ("from .validation.", "from dsl_validate."),
    ("from .validation import", "from dsl_validate import"),
    ("from .conversation_artifacts import", "from testql_conversations.artifacts import"),
    ("from .compose_generator import", "from nlp2dsl_stack import"),
    ("from .artifacts import", "from nlp2dsl_artifacts import"),
    ("from .system_map_render import", "from env2llm.render.doql import"),
    ("from .system_map_bridge import", "from env2llm.bridge import"),
    ("from .system_map_generator import", "from env2llm.generate import"),
    ("from .system_map_runtimes import", "from env2llm.runtimes import"),
    ("from .system_map_ir import", "from env2llm.ir import"),
    ("from .doql_registry import", "from env2llm.registry import"),
    ("from .artifact_layout import", "from env2llm.layout import"),
    ("from .example_bootstrap import", "from env2llm.bootstrap import"),
    ("from .doql_context import", "from env2llm.doql_context import"),
]


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in TEXT_REPLACEMENTS:
        text = text.replace(old, new)
    if "nlp2dsl_sdk" in str(path) and "nlp2dsl_sdk/" in str(path):
        for old, new in RELATIVE_REPLACEMENTS:
            text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    roots = [ROOT, KORU] if KORU.is_dir() else [ROOT]
    changed: list[Path] = []
    for base in roots:
        for path in base.rglob("*.py"):
            if ".venv" in path.parts or "venv" in path.parts or "packages/" in str(path) and "/src/" in str(path):
                continue
            if path.name == "migrate-direct-imports.py":
                continue
            if migrate_file(path):
                changed.append(path)
    print(f"Updated {len(changed)} files")
    for p in sorted(changed)[:30]:
        print(f"  {p.relative_to(p.anchor) if p.is_absolute() else p}")
    if len(changed) > 30:
        print(f"  ... and {len(changed) - 30} more")


if __name__ == "__main__":
    main()
