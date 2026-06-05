"""Query normalization."""

from __future__ import annotations

import re


class QueryNormalizer:
    """Lightweight normalizer; full Polish support migrates from nlp2cmd later."""

    _WS = re.compile(r"\s+")

    def normalize(self, query: str) -> str:
        text = (query or "").strip()
        text = self._WS.sub(" ", text)
        return text
