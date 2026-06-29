"""NL → DSL line (no side effects)."""

from __future__ import annotations

import re

from uri2nlp2dsl.resolve import resolve_nl


def _intent(prompt: str) -> str:
    text = prompt.lower()
    if any(w in text for w in ("validate", "waliduj", "sprawdź", "sprawdz")):
        return "VALIDATE"
    if any(w in text for w in ("execute", "uruchom", "wykonaj", "run")):
        return "EXECUTE"
    if any(w in text for w in ("simulate", "symuluj", "dry")):
        return "SIMULATE"
    if any(w in text for w in ("generate", "wygeneruj", "stwórz", "stworz", "create")):
        return "GENERATE"
    if any(w in text for w in ("plan", "zaplanuj")):
        return "PLAN"
    if any(w in text for w in ("parse", "parsuj", "rozpoznaj")):
        return "PARSE"
    if any(w in text for w in ("health", "status")):
        return "HEALTH"
    if any(w in text for w in ("observe", "registry", "environment")):
        return "OBSERVE"
    if any(w in text for w in ("compose", "stack", "docker")):
        return "COMPOSE"
    if any(w in text for w in ("draft", "kontrakt", "contract")):
        return "DRAFT"
    return "PARSE"


def to_dsl(prompt: str, *, mode: str = "auto") -> str:
    """Convert NL prompt to a single DSL line without executing."""
    intent = _intent(prompt)
    text = prompt.strip().strip('"').strip("'")

    if intent == "VALIDATE":
        m = re.search(r"([\w./-]+\.(?:json|yaml|yml))", prompt)
        if m:
            return f"VALIDATE FILE {m.group(1)}"
        return f'VALIDATE "{text}"'

    if intent in {"EXECUTE", "SIMULATE", "GENERATE", "PLAN", "PARSE"}:
        line = f'{intent} "{text}" MODE {mode}'
        m = re.search(r"\bout\s+(\S+)", prompt, re.IGNORECASE)
        if m:
            line += f" OUT {m.group(1)}"
        if intent == "SIMULATE" or "dry" in prompt.lower():
            line += " DRY_RUN true"
        return line

    if intent == "OBSERVE":
        m = re.search(r"(?:observe|registry)\s+(\S+)", prompt, re.IGNORECASE)
        target = m.group(1) if m else "."
        return f"OBSERVE {target}"

    if intent == "COMPOSE":
        m = re.search(r"(?:profile|stack)\s+(\S+)", prompt, re.IGNORECASE)
        profile = m.group(1) if m else "default"
        return f"COMPOSE PROFILE {profile}"

    if intent == "DRAFT":
        m = re.search(r"(?:draft|kontrakt)\s+(\S+)", prompt, re.IGNORECASE)
        name = m.group(1) if m else text.split()[-1]
        return f"DRAFT {name}"

    hits = resolve_nl(prompt)
    from uri2nlp2dsl.decode import uri_to_dsl

    return uri_to_dsl(hits[0].uri)
