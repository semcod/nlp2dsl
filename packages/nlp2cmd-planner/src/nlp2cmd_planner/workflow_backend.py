"""Optional nlp2dsl backend workflow/from-text client."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def workflow_backend_enabled() -> bool:
    flag = os.getenv("NLP2CMD_NLP2DSL_WORKFLOW", "0").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def workflow_backend_url() -> str:
    return os.getenv(
        "NLP2DSL_BACKEND_URL",
        os.getenv("NLP2DSL_API_URL", os.getenv("BACKEND_URL", "http://localhost:8010")),
    ).rstrip("/")


def workflow_run_path() -> str:
    path = os.getenv("NLP2DSL_WORKFLOW_RUN_PATH", "/workflow/run")
    return path if path.startswith("/") else f"/{path}"


def fetch_workflow_from_text(query: str) -> dict[str, Any] | None:
    """Fetch workflow DSL from nlp2dsl backend (invoice-style NL actions)."""
    if not query.strip():
        return None

    payload = json.dumps(
        {"text": query, "execute": False, "mode": "auto"},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{workflow_backend_url()}/workflow/from-text",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    timeout = float(os.getenv("NLP2DSL_TIMEOUT", "10"))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data if isinstance(data, dict) else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
