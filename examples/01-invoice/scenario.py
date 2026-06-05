"""Scenariusz: wysyłanie faktury — logika przykładu 01-invoice."""

from __future__ import annotations

from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.preview import (
    ensure_services,
    execute_from_text,
    preview_text_examples,
)

INVOICE_PROMPT = "Wyślij fakturę na 1500 PLN do klient@firma.pl"


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Przykład: Wysyłanie Faktury ===\n")

    if not ensure_services(client):
        return {}

    preview_text_examples(client, "", [INVOICE_PROMPT], finalize_artifacts=False)

    result = execute_from_text(client, INVOICE_PROMPT, label="Wykonywanie z zapytania NLP")

    if result.get("status") == "executed":
        execution = result.get("result", {})
        if execution.get("status") == "completed":
            step = execution.get("steps", [{}])[0]
            if step.get("status") == "completed":
                inv_id = step.get("result", {}).get("invoice_id", "?")
                print(f"\n🎉 Faktura wysłana! ID: {inv_id}")
            else:
                print(f"\n❌ Błąd: {step.get('error')}")
        else:
            print(f"\n❌ Workflow nie powiódł się: {execution.get('error')}")
    else:
        print(f"\n❌ Nie udało się wykonać: {result.get('error', result.get('status'))}")

    from nlp2dsl_sdk.artifacts import get_example_writer

    writer = get_example_writer()
    if writer:
        writer.finalize(client)

    return result
