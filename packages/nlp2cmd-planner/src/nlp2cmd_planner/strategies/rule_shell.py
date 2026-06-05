"""Rule-based shell planning (MVP)."""

from __future__ import annotations

import re

from pact_ir import ExecutionPlanIR, IntentIR, PlanStep, TargetKind

_FILE_SEARCH_INTENTS = frozenset({"file_search", "find", "search"})
_LIST_INTENTS = frozenset({"list", "ls", "dir"})

# e.g. *.py, **/*.ts, foo*.bar
_GLOB_RE = re.compile(r"(\*\*\/[\w.*-]+|\*\.[\w]+|[\w.*-]*\*[\w.*-]*)")
_PATH_SUFFIX_RE = re.compile(
    r"\b(?:w|we|in|inside|under|from|katalogu|folderze|directory)\s+([^\s,]+)\s*$",
    re.IGNORECASE,
)


def _parse_file_search(intent: IntentIR) -> tuple[str, str]:
    """Resolve path and glob from entities or query text."""
    path = intent.entities.get("path") or intent.entities.get("directory")
    pattern = (
        intent.entities.get("pattern")
        or intent.entities.get("glob")
        or intent.entities.get("name")
    )

    query = intent.query
    if not pattern:
        match = _GLOB_RE.search(query)
        if match:
            pattern = match.group(1)

    if not path:
        match = _PATH_SUFFIX_RE.search(query)
        if match:
            path = match.group(1)

    return str(path or "."), str(pattern or "*")


class RuleShellPlanStrategy:
    name = "rule_shell"

    def supports(self, intent: IntentIR) -> bool:
        if intent.target_kind != TargetKind.SHELL:
            return False
        return intent.intent in _FILE_SEARCH_INTENTS | _LIST_INTENTS

    def plan(self, intent: IntentIR) -> ExecutionPlanIR:
        if intent.intent in _FILE_SEARCH_INTENTS:
            path, pattern = _parse_file_search(intent)
            dsl = f'find {path} -name "{pattern}"'
            step = PlanStep(
                id="s1",
                action="shell_find",
                target_kind=TargetKind.SHELL,
                params={"path": path, "name": pattern},
                dsl=dsl,
                description="Find files by pattern",
            )
        else:
            path = intent.entities.get("path", ".")
            dsl = f"ls -la {path}".rstrip() if path != "." else "ls -la"
            step = PlanStep(
                id="s1",
                action="shell_list",
                target_kind=TargetKind.SHELL,
                params={"path": path},
                dsl=dsl,
                description="List directory",
            )
        return ExecutionPlanIR.from_intent(intent, steps=[step], source=self.name)
