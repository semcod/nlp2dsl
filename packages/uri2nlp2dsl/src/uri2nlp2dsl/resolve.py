"""NL hints → nlp2dsl://cmd URI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from uri2nlp2dsl.uri import build_cmd_uri


@dataclass
class ResolveHit:
    uri: str
    verb: str
    score: float = 1.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"uri": self.uri, "verb": self.verb, "score": self.score, "reason": self.reason}


_VERB_HINTS: list[tuple[str, list[str]]] = [
    ("PARSE", ["parse", "parsuj", "rozpoznaj", "intent"]),
    ("PLAN", ["plan", "zaplanuj", "workflow"]),
    ("VALIDATE", ["validate", "waliduj", "sprawdź", "sprawdz"]),
    ("EXECUTE", ["execute", "uruchom", "wykonaj", "run"]),
    ("GENERATE", ["generate", "wygeneruj", "stwórz", "stworz"]),
    ("HEALTH", ["health", "status", "zdrowie"]),
    ("OBSERVE", ["observe", "registry", "mapa", "environment"]),
    ("COMPOSE", ["compose", "stack", "docker"]),
    ("DRAFT", ["draft", "kontrakt", "contract"]),
]


def resolve_nl(prompt: str) -> list[ResolveHit]:
    text = prompt.lower()
    hits: list[ResolveHit] = []
    for verb, keywords in _VERB_HINTS:
        if any(kw in text for kw in keywords):
            params: dict[str, str] = {"text": prompt.strip()}
            mode = "llm" if any(w in text for w in ("llm", "ai", "gpt")) else "auto"
            params["mode"] = mode
            hits.append(ResolveHit(uri=build_cmd_uri(verb, **params), verb=verb, reason="keyword"))
    if not hits:
        hits.append(ResolveHit(uri=build_cmd_uri("PARSE", text=prompt.strip(), mode="auto"), verb="PARSE", score=0.5, reason="default"))
    return hits
