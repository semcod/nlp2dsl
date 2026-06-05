"""Map nlp2cmd detection domains/intents to pact-ir types."""

from __future__ import annotations

from pact_ir import ExecutionRisk, TargetKind

_DOMAIN_TO_TARGET: dict[str, TargetKind] = {
    "shell": TargetKind.SHELL,
    "sql": TargetKind.SQL,
    "docker": TargetKind.SHELL,
    "kubernetes": TargetKind.SHELL,
    "browser": TargetKind.BROWSER,
    "utility": TargetKind.SHELL,
    "networking_ext": TargetKind.SHELL,
    "networking": TargetKind.SHELL,
    "multi_step": TargetKind.BROWSER,
    "unknown": TargetKind.UNKNOWN,
}

_DESTRUCTIVE_INTENTS = frozenset({
    "delete",
    "remove",
    "drop_table",
    "truncate",
    "process_kill",
    "reboot",
    "service_stop",
})


def domain_to_target_kind(domain: str) -> TargetKind:
    return _DOMAIN_TO_TARGET.get((domain or "").lower(), TargetKind.UNKNOWN)


def intent_to_execution_risk(intent: str, *, domain: str = "") -> ExecutionRisk:
    name = (intent or "").lower()
    if name in _DESTRUCTIVE_INTENTS:
        return ExecutionRisk.DESTRUCTIVE
    if domain == "kubernetes" and name in {"scale", "delete"}:
        return ExecutionRisk.HIGH
    if domain == "docker" and name in {"stop", "remove", "restart"}:
        return ExecutionRisk.MEDIUM
    return ExecutionRisk.LOW
