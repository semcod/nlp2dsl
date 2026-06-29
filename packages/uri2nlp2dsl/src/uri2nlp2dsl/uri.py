"""Build and parse nlp2dsl:// URIs."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse


SCHEME = "nlp2dsl"


@dataclass
class Nlp2dslUri:
    verb: str
    params: dict[str, str]
    target: str = ""

    @property
    def is_cmd(self) -> bool:
        return True


def parse_uri(uri: str) -> Nlp2dslUri:
    parsed = urlparse(uri)
    if parsed.scheme != SCHEME:
        raise ValueError(f"expected {SCHEME}:// URI, got {parsed.scheme}")
    path = parsed.path.strip("/")
    parts = path.split("/") if path else []
    if len(parts) >= 2 and parts[0] == "cmd":
        verb = parts[1].upper()
    elif parts:
        verb = parts[-1].upper()
    else:
        raise ValueError("URI missing verb path")
    qs = {k: unquote(v[0]) for k, v in parse_qs(parsed.query).items() if v}
    target = qs.pop("target", "")
    return Nlp2dslUri(verb=verb, params=qs, target=target)


def build_cmd_uri(verb: str, **params: str) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items() if v)
    base = f"{SCHEME}://cmd/{verb.upper()}"
    return f"{base}?{query}" if query else base
