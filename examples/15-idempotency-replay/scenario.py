"""Demonstracja idempotencji side effects — replay bez ponownego wykonania."""

from __future__ import annotations

from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.preview import ensure_services, print_execution_result

IDEMPOTENCY_KEY = "example-15-invoice-replay"


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Przykład: Idempotencja side effects ===\n")

    if not ensure_services(client):
        return {}

    text = "Wyślij fakturę na 500 PLN do test@firma.pl"
    print(f"▶ Pierwsze wykonanie (from-text, key={IDEMPOTENCY_KEY})")
    first = client.workflow_from_text(
        text,
        execute=True,
        mode="rules",
        idempotency_key=IDEMPOTENCY_KEY,
    )
    if first.get("status") != "executed":
        print(f"⚠️  status={first.get('status')} missing={first.get('missing_fields')}")
        return {"first": first}

    dsl = first.get("dsl")
    if not isinstance(dsl, dict):
        print("⚠️  Brak DSL w odpowiedzi from-text")
        return {"first": first}

    print_execution_result(first.get("result", {}))
    print(f"   idempotent_replay={first.get('idempotent_replay', False)}")

    print(f"\n▶ Drugie wykonanie (ten sam DSL + key — oczekiwany replay)")
    second = client.workflow_execute(
        dsl,
        idempotency_key=IDEMPOTENCY_KEY,
        skip_policy_check=True,
    )
    print_execution_result(second.get("result", {}))
    replay = bool(second.get("idempotent_replay"))
    print(f"   idempotent_replay={replay}")

    if replay:
        print("\n✅ Replay OK — side effect nie wykonany ponownie")
    else:
        print("\n❌ Brak replay — idempotency store backendu (POSTGRES_URL / ten sam worker)")
        raise SystemExit(1)

    return {"first": first, "second": second, "replay_ok": replay}
