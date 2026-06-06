"""Fast-path intent detection helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from nlp2cmd_intent.keywords.fast_path_terms import (
    BROWSER_COMPLEX,
    BROWSER_CONTEXT_SIGNALS,
    BROWSER_PHRASE_PATTERNS,
    DOCKER_CONTAINER_ACTIONS,
    DOCKER_TERMS,
    K8S_TERMS,
    LIMIT_KEYWORDS,
    SHELL_TERMS,
    SQL_EXACT,
    SQL_NL,
    TABLE_NAME_KEYWORDS,
    USER_TABLE_KEYWORDS,
)
from nlp2cmd_intent.keywords.keyword_patterns import KeywordPatterns


@dataclass(frozen=True)
class FastPathHit:
    domain: str
    intent: str
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    matched_keyword: str = ""


ExplicitOverride = tuple[str, str, str, str]


def normalize_url(raw: str) -> str:
    u = (raw or "").strip().strip('""')
    if not u:
        return u
    if u.startswith(("http://", "https://", "file://")):
        return u
    if u.startswith("www."):
        return f"https://{u}"
    if re.match(r"^[a-zA-Z0-9][\w\-\.]*\.[a-zA-Z]{2,}(?:/[^\s\'\"]*)?$", u):
        return f"https://{u}"
    return u


def match_explicit_overrides(
    overrides: Sequence[ExplicitOverride],
    text_normalized: str,
) -> Optional[FastPathHit]:
    for kw, domain, intent, matched_kw in overrides:
        if kw in text_normalized:
            return FastPathHit(domain=domain, intent=intent, confidence=0.95, matched_keyword=matched_kw)
    return None


def match_exact_commands(text_lower: str) -> Optional[FastPathHit]:
    _EXACT_COMMANDS = {
        "ps": ("shell", "list_processes"),
        "ls": ("shell", "list"),
        "top": ("shell", "list_processes"),
        "df": ("shell", "disk_usage"),
        "du": ("shell", "disk_usage"),
        "pwd": ("shell", "list"),
    }
    stripped = text_lower.strip()
    if stripped in _EXACT_COMMANDS:
        domain, intent = _EXACT_COMMANDS[stripped]
        return FastPathHit(domain=domain, intent=intent, confidence=0.95, matched_keyword=stripped)
    return None


def _term_hit(
    text_lower: str,
    terms: Sequence[tuple[str, str]],
    *,
    domain: str,
    confidence: float,
) -> Optional[FastPathHit]:
    for kw, intent in terms:
        if kw in text_lower:
            return FastPathHit(domain=domain, intent=intent, confidence=confidence, matched_keyword=kw)
    return None


def _match_sql_exact(text_lower: str) -> Optional[FastPathHit]:
    for kw, intent in SQL_EXACT.items():
        if kw in text_lower:
            return FastPathHit(domain="sql", intent=intent, confidence=0.95, matched_keyword=kw)
    return None


def _match_docker(text_lower: str) -> Optional[FastPathHit]:
    if hit := _term_hit(text_lower, DOCKER_TERMS, domain="docker", confidence=0.9):
        return hit
    return _term_hit(text_lower, DOCKER_CONTAINER_ACTIONS, domain="docker", confidence=0.88)


def _k8s_entities(text_lower: str, intent: str) -> dict[str, Any]:
    if intent == "get" and "namespace" in text_lower:
        ns_match = re.search(r"namespace\s+(\S+)", text_lower)
        return {"namespace": ns_match.group(1)} if ns_match else {}
    if intent == "scale" and ("replik" in text_lower or "replica" in text_lower):
        replica_match = re.search(r"(\d+)\s+(?:replik|repliki|replicas)", text_lower)
        if replica_match:
            return {"replicas": replica_match.group(1)}
    return {}


def _match_k8s(text_lower: str) -> Optional[FastPathHit]:
    for kw, intent in K8S_TERMS:
        if kw not in text_lower:
            continue
        entities = _k8s_entities(text_lower, intent)
        return FastPathHit(
            domain="kubernetes",
            intent=intent,
            confidence=0.9,
            entities=entities,
            matched_keyword=kw,
        )
    return None


def _shell_find_entities(text_lower: str) -> dict[str, Any]:
    if not ("*" in text_lower or ".py" in text_lower or ".txt" in text_lower or ".json" in text_lower):
        return {}
    file_pattern_match = re.search(r"(\*\\\?[a-zA-Z0-9]+|\*[a-zA-Z0-9]+)", text_lower)
    if file_pattern_match:
        return {"pattern": file_pattern_match.group(1)}
    if ".py" in text_lower:
        return {"pattern": "*.py"}
    if ".txt" in text_lower:
        return {"pattern": "*.txt"}
    if ".json" in text_lower:
        return {"pattern": "*.json"}
    return {}


def _shell_intent_entities(text_lower: str, intent: str) -> dict[str, Any]:
    if intent == "find":
        return _shell_find_entities(text_lower)
    if intent == "process_kill":
        pid_match = re.search(r"(?:pid\s*)?(\d{2,})", text_lower)
        return {"pid": pid_match.group(1)} if pid_match else {}
    if intent == "create_dir":
        dir_match = re.search(r"(?:katalog|folder|directory)\s+([\w./_-]+)", text_lower)
        return {"directory": dir_match.group(1)} if dir_match else {}
    if intent == "permissions_chmod":
        entities: dict[str, Any] = {}
        perm_match = re.search(r"\b(\d{3,4})\b", text_lower)
        if perm_match:
            entities["permissions"] = perm_match.group(1)
        file_match = re.search(r"(?:pliku?\s+|of\s+|file\s+)([\w./_-]+)", text_lower)
        if file_match:
            entities["file"] = file_match.group(1)
        return entities
    if intent == "compress_tar":
        src_match = re.search(r"(?:folder|katalog|directory)\s+([\w./_-]+)", text_lower)
        return {"source": src_match.group(1)} if src_match else {}
    return {}


def _match_shell(text_lower: str) -> Optional[FastPathHit]:
    has_browser_context = any(s in text_lower for s in BROWSER_CONTEXT_SIGNALS)
    for kw, intent in SHELL_TERMS.items():
        if kw not in text_lower:
            continue
        if has_browser_context and intent in ("copy", "move", "remove"):
            continue
        entities = _shell_intent_entities(text_lower, intent)
        return FastPathHit(
            domain="shell",
            intent=intent,
            confidence=0.88,
            entities=entities,
            matched_keyword=kw,
        )
    return None


def _sql_nl_table_entities(text_lower: str, kw: str) -> dict[str, Any]:
    if kw in TABLE_NAME_KEYWORDS:
        table_match = re.search(rf"{re.escape(kw)}\s+(\w+)", text_lower)
        return {"table": table_match.group(1)} if table_match else {}
    if " tabeli " in text_lower or " table " in text_lower:
        table_match = re.search(r"(\w+)\s+tabeli|tabeli\s+(\w+)|(\w+)\s+table|table\s+(\w+)", text_lower)
        if table_match:
            table_name = next((group for group in table_match.groups() if group), None)
            if table_name:
                return {"table": table_name}
    if kw in USER_TABLE_KEYWORDS:
        return {"table": "users"}
    return {}


def _sql_nl_entities(text_lower: str, kw: str) -> dict[str, Any]:
    entities = _sql_nl_table_entities(text_lower, kw)
    if "gdzie" in text_lower or "where" in text_lower:
        where_match = re.search(r"(?:gdzie|where)\s+([^,.!?]+)", text_lower)
        if where_match:
            entities["where"] = where_match.group(1).strip()
    if kw in LIMIT_KEYWORDS:
        limit_match = re.search(r"(\d+)\s+(?:rekordów|rekordow|records|wierszy|rows)", text_lower)
        if limit_match:
            entities["limit"] = limit_match.group(1)
    return entities


def _match_sql_nl(text_lower: str) -> Optional[FastPathHit]:
    for kw, intent in SQL_NL:
        if kw not in text_lower:
            continue
        entities = _sql_nl_entities(text_lower, kw)
        return FastPathHit(
            domain="sql",
            intent=intent,
            confidence=0.85,
            entities=entities,
            matched_keyword=kw,
        )
    return None


def _browser_url_entities(text_lower: str) -> dict[str, Any]:
    url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
    if url_match:
        return {"url": normalize_url(url_match.group(1))}
    domain_in_text = re.search(
        r"\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|co|de|uk|eu)(?:/[^\s'\"]*)?)",
        text_lower,
    )
    if domain_in_text:
        return {"url": normalize_url(domain_in_text.group(1))}
    return {}


def _match_browser_phrases(text_lower: str) -> Optional[FastPathHit]:
    for pattern, domain, intent in BROWSER_PHRASE_PATTERNS:
        if not re.search(pattern, text_lower):
            continue
        return FastPathHit(
            domain=domain,
            intent=intent,
            confidence=0.92,
            entities=_browser_url_entities(text_lower),
            matched_keyword=pattern,
        )
    return None


def _match_browser_complex(text_lower: str) -> Optional[FastPathHit]:
    for kw, domain, intent in BROWSER_COMPLEX:
        if kw not in text_lower:
            continue
        url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
        entities = {"url": normalize_url(url_match.group(1))} if url_match else {}
        return FastPathHit(domain=domain, intent=intent, confidence=0.95, entities=entities, matched_keyword=kw)
    return None


def _match_url_navigate(text_lower: str) -> Optional[FastPathHit]:
    url_match = re.search(r"\b(https?://[^\s'\"]+)", text_lower)
    if url_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.95,
            entities={"url": normalize_url(url_match.group(1))},
        )
    www_match = re.search(r"\b(www\.[^\s'\"]+)", text_lower)
    if www_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.92,
            entities={"url": normalize_url(www_match.group(1))},
        )
    domain_match = re.search(
        r"\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|ai|dev|pl|app|de|uk|eu|gov|edu|tv|co)(?:/[^\s'\"]*)?)\b",
        text_lower,
    )
    if domain_match:
        return FastPathHit(
            domain="browser",
            intent="navigate",
            confidence=0.9,
            entities={"url": normalize_url(domain_match.group(1))},
        )
    return None


def _match_browser_keywords(text_lower: str, patterns: KeywordPatterns) -> Optional[FastPathHit]:
    if any(kw in text_lower for kw in patterns.fast_path_browser_keywords):
        return FastPathHit(domain="browser", intent="web_action", confidence=0.8)
    return None


def _match_search_keywords(text_lower: str, patterns: KeywordPatterns) -> Optional[FastPathHit]:
    if any(kw in text_lower for kw in patterns.fast_path_search_keywords):
        return FastPathHit(domain="shell", intent="search_web", confidence=0.8)
    return None


def run_domain_fast_path_after_exact(
    text_lower: str,
    patterns: KeywordPatterns,
) -> Optional[FastPathHit]:
    matchers = (
        lambda: _match_sql_exact(text_lower),
        lambda: _match_docker(text_lower),
        lambda: _match_k8s(text_lower),
        lambda: _match_shell(text_lower),
        lambda: _match_sql_nl(text_lower),
        lambda: _match_browser_phrases(text_lower),
        lambda: _match_browser_complex(text_lower),
        lambda: _match_url_navigate(text_lower),
        lambda: _match_browser_keywords(text_lower, patterns),
        lambda: _match_search_keywords(text_lower, patterns),
    )
    for matcher in matchers:
        if hit := matcher():
            return hit
    return None


def fast_path_detect(
    text_lower: str,
    patterns: KeywordPatterns,
    *,
    domain_rules: bool = True,
) -> Optional[FastPathHit]:
    text_normalized = " ".join(text_lower.split())
    if hit := match_explicit_overrides(patterns.explicit_overrides, text_normalized):
        return hit
    if hit := match_exact_commands(text_lower):
        return hit
    if not domain_rules:
        return None
    return run_domain_fast_path_after_exact(text_lower, patterns)
