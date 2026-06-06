"""Example: webhook trigger → NLP2DSL plan."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TRIGGER_URL = os.getenv("NLP2DSL_TRIGGER_URL", "http://localhost:8070").rstrip("/")
BACKEND_URL = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")


def run() -> None:
    print("=== 18-trigger-webhook ===\n")

    # Fallback: call backend directly if trigger-service not running
    use_trigger = False
    try:
        health = httpx.get(f"{TRIGGER_URL}/health", timeout=3.0)
        if health.status_code == 200 and health.json().get("service") == "trigger-service":
            use_trigger = True
    except (httpx.RequestError, ValueError, KeyError):
        use_trigger = False
    if not use_trigger:
        print(f"⚠️  Trigger service unavailable at {TRIGGER_URL} — using backend /workflow/plan")

    query = "Codziennie raport sprzedaży PDF i email do manager@firma.pl"

    if use_trigger:
        resp = httpx.post(
            f"{TRIGGER_URL}/triggers/webhook/scheduled-report",
            json={"text": query, "mode": "rules"},
            timeout=30.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        print(f"Trigger: {payload['trigger_id']} source={payload['source']}")
        result = payload["result"]
    else:
        resp = httpx.post(
            f"{BACKEND_URL}/workflow/plan",
            json={"text": query, "mode": "rules"},
            timeout=30.0,
        )
        resp.raise_for_status()
        result = resp.json()

    workflow = result.get("workflow") or result.get("dsl")
    assert workflow, "Expected workflow in plan response"
    print(f"✅ Workflow: {workflow.get('name')} trigger={workflow.get('trigger')}")
    print(f"   Steps: {len(workflow.get('steps', []))}")


if __name__ == "__main__":
    run()
