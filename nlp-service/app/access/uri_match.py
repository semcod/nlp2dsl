"""Dopasowanie URI do wzorców (glob / prefix) — standardowe usługi i schematy."""

from __future__ import annotations

import fnmatch
from urllib.parse import urlparse


def normalize_uri(uri: str) -> str:
    return (uri or "").strip()


def uri_matches(pattern: str, uri: str) -> bool:
    """
    Wzorce z YAML:
      mullm://**           → wszystkie zasoby Mullm
      mullm://ticket/*     → tickety
      file:///home/user/** → pliki użytkownika
      https://mail.example.com/**
    """
    pattern = (pattern or "").strip()
    uri = normalize_uri(uri)
    if not pattern or not uri:
        return False
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return uri.startswith(prefix)
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return uri.startswith(prefix) and (len(uri) == len(prefix) or uri[len(prefix)] in "/:")
    glob_pat = pattern.replace("**", "*")
    return fnmatch.fnmatchcase(uri, glob_pat)


def scheme_allowed(uri: str, allowed_schemes: list[str]) -> bool:
    if not allowed_schemes:
        return True
    parsed = urlparse(uri)
    scheme = parsed.scheme or ""
    if not scheme and uri.startswith("/"):
        return "file" in allowed_schemes
    return scheme in allowed_schemes
