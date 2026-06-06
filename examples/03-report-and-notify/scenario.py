"""Scenariusz: raport + powiadomienia — logika przykładu 03."""

from __future__ import annotations

from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.preview import (
    ensure_services,
    execute_from_text,
    preview_text_examples,
)

REPORT_TEXT_EXAMPLES: tuple[str, ...] = (
    "Co tydzień generuj raport sprzedaży w PDF i wyślij email do manager@firma.pl",
    "Generuj raport HR i powiadom na #hr",
    "Miesięczny raport finansów do CFO i teamu",
    "Raport kwartalny sprzedaży w CSV i wyślij go do #sales",
)

# Composite z trzema kanałami — rozpoznawany przez NLP (bez generate_report_and_notify)
REPORT_EXECUTION_QUERY = (
    "Co tydzień generuj raport sprzedaży PDF, wyślij email do manager@firma.pl "
    "i powiadom na Slack #sales"
)


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Przykład: Raport i Powiadomienia ===\n")

    if not ensure_services(client):
        return {}

    preview_text_examples(client, "", REPORT_TEXT_EXAMPLES, finalize_artifacts=False)

    result = execute_from_text(
        client,
        REPORT_EXECUTION_QUERY,
        label="Wykonywanie workflow z wieloma krokami",
    )

    dsl = result.get("dsl") if isinstance(result.get("dsl"), dict) else None
    if dsl and dsl.get("steps"):
        from workflow_export.publish import (
            catalog_from_nlp_client,
            export_workflow_publish_layer,
            print_publish_summary,
            validate_publish_layer,
        )
        from nlp2dsl_artifacts import example_artifact_root

        import os

        artifact_root = example_artifact_root(os.environ.get("NLP2DSL_EXAMPLE_DIR", "."))
        print("\n📦 Export markpact + pactown (full_report_flow):")
        bundle = export_workflow_publish_layer(
            artifact_root,
            dsl,
            catalog_from_nlp_client(client),
            source_query=REPORT_EXECUTION_QUERY,
            title=f"{dsl.get('name', 'full_report_flow')} — report + email + slack",
        )
        print_publish_summary(bundle, validation=validate_publish_layer(bundle))

    if result.get("status") == "executed":
        execution = result.get("result", {})
        if execution.get("status") == "completed":
            print("\n🎉 Workflow wykonany pomyślnie!")
        else:
            print(f"\n❌ Workflow nie powiódł się: {execution.get('error')}")
    else:
        print(f"\n❌ Status: {result.get('status')} — {result.get('missing_fields', [])}")

    from nlp2dsl_artifacts import get_example_writer

    writer = get_example_writer()
    if writer:
        writer.record(REPORT_EXECUTION_QUERY, result, mode="auto")
        writer.finalize(client)

    return result
