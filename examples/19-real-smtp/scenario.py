"""Example: send_email via real SMTP (MailHog) when SMTP_HOST is set."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nlp2dsl_sdk.client import NLP2DSLClient

BACKEND_URL = os.getenv("NLP2DSL_BACKEND_URL", "http://localhost:8010").rstrip("/")
MAILHOG_API = os.getenv("MAILHOG_API_URL", "http://localhost:18025").rstrip("/")


def _mailhog_available() -> bool:
    try:
        resp = httpx.get(f"{MAILHOG_API}/api/v2/messages", timeout=2.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


def run() -> None:
    print("=== 19-real-smtp ===\n")

    workflow = {
        "name": "smtp_test",
        "trigger": "manual",
        "steps": [
            {
                "action": "send_email",
                "config": {
                    "to": "klient@firma.pl",
                    "subject": "Test SMTP NLP2DSL",
                    "body": "Wiadomość testowa z przykładu 19-real-smtp.",
                },
            }
        ],
    }

    with NLP2DSLClient.from_env() as client:
        payload = client.workflow_execute(
            workflow,
            idempotency_key=f"example-19-smtp-{int(time.time())}",
            skip_access_check=True,
            skip_policy_check=True,
        )

    if payload.get("status") == "blocked":
        print(f"⚠️  Policy blocked: {payload.get('message', '')[:200]}")
        print("   Uruchom z skip_access_check lub przebuduj backend z ACL demo.")
        return

    wf_result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    steps = wf_result.get("steps") or payload.get("steps") or []

    assert steps, f"Expected worker steps in result, got keys: {list(payload.keys())}"

    step_result = steps[0].get("result") or {}
    transport = step_result.get("transport", "unknown")
    print(f"Transport: {transport}")
    print(f"Sent to: {step_result.get('sent_to')}")

    if transport == "smtp" and _mailhog_available():
        msgs = httpx.get(f"{MAILHOG_API}/api/v2/messages", timeout=5.0).json()
        total = int(msgs.get("total", 0))
        print(f"✅ MailHog messages: {total}")
        assert total >= 1, "Expected at least one message in MailHog"
    elif transport == "simulated":
        print("⚠️  SMTP_HOST not set on worker — simulated delivery (OK for CI)")
    else:
        print(f"✅ Email step completed (transport={transport})")

    print("\n--- Podsumowanie ---")
    print(f"   execute status: {payload.get('status', wf_result.get('status'))}")
    print(f"   transport: {transport}")


if __name__ == "__main__":
    run()
