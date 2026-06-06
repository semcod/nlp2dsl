"""JSON loaders for KeywordPatterns configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)

PatternMap = Dict[str, Dict[str, List[str]]]
ExplicitOverride = Tuple[str, str, str, str]


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        logger.warning("Failed to load JSON from %s: %s", path, exc)
        return None
    return payload if isinstance(payload, dict) else None


def clean_string_list(
    items: list[Any],
    *,
    normalizer: Callable[[str], str],
) -> list[str]:
    return [normalizer(item.strip()) for item in items if isinstance(item, str) and item.strip()]


def merge_patterns_payload(
    base: PatternMap,
    payload: dict[str, Any],
    *,
    normalizer: Callable[[str], str],
    dedupe: Callable[[list[str]], list[str]],
) -> None:
    for domain, intents in payload.items():
        if domain == "$schema" or not isinstance(intents, dict):
            continue
        bucket = base.setdefault(domain, {})
        if not isinstance(bucket, dict):
            continue
        for intent, keywords in intents.items():
            if not isinstance(intent, str) or not intent.strip() or not isinstance(keywords, list):
                continue
            clean = clean_string_list(keywords, normalizer=normalizer)
            if not clean:
                continue
            key = intent.strip()
            prev = bucket.get(key)
            prev_list = prev if isinstance(prev, list) else []
            bucket[key] = dedupe([*clean, *prev_list])


def parse_domain_boosters(
    payload: dict[str, Any],
    *,
    normalizer: Callable[[str], str],
) -> dict[str, list[str]]:
    boosters = payload.get("domain_boosters")
    if not isinstance(boosters, dict):
        return {}
    out: dict[str, list[str]] = {}
    for domain, keywords in boosters.items():
        if isinstance(domain, str) and isinstance(keywords, list):
            clean = clean_string_list(keywords, normalizer=normalizer)
            if clean:
                out[domain] = clean
    return out


def parse_priority_intents(
    payload: dict[str, Any],
    *,
    normalizer: Callable[[str], str],
) -> dict[str, list[str]]:
    priority = payload.get("priority_intents")
    if not isinstance(priority, dict):
        return {}
    out: dict[str, list[str]] = {}
    for domain, intents in priority.items():
        if isinstance(domain, str) and isinstance(intents, list):
            clean = clean_string_list(intents, normalizer=normalizer)
            if clean:
                out[domain] = clean
    return out


def parse_fast_path_settings(
    payload: dict[str, Any],
    *,
    normalizer: Callable[[str], str],
    dedupe: Callable[[list[str]], list[str]],
) -> tuple[list[str], list[str], set[str]]:
    fast_path = payload.get("fast_path")
    if not isinstance(fast_path, dict):
        return [], [], set()

    browser_keywords: list[str] = []
    browser = fast_path.get("browser_keywords")
    if isinstance(browser, list):
        browser_keywords = dedupe(clean_string_list(browser, normalizer=normalizer))

    search_keywords: list[str] = []
    search = fast_path.get("search_keywords")
    if isinstance(search, list):
        search_keywords = dedupe(clean_string_list(search, normalizer=normalizer))

    common_images: set[str] = set()
    images = fast_path.get("common_images")
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str) and item.strip():
                common_images.add(item.strip().lower())

    return browser_keywords, search_keywords, common_images


def parse_explicit_overrides(payload: dict[str, Any]) -> list[ExplicitOverride]:
    rows = payload.get("explicit_overrides")
    if not isinstance(rows, list):
        return []
    loaded: list[ExplicitOverride] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        keyword = str(row.get("keyword", "")).strip().lower()
        domain = str(row.get("domain", "")).strip()
        intent = str(row.get("intent", "")).strip()
        matched = str(row.get("matched_keyword", keyword)).strip()
        if keyword and domain and intent:
            loaded.append((keyword, domain, intent, matched))
    return loaded
