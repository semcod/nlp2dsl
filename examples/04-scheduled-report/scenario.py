"""Scenariusz: zaplanowane raporty — logika przykładu 04."""

from __future__ import annotations

from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.preview import (
    ensure_services,
    execute_from_text,
    preview_text_examples,
    print_workflow_preview,
)

# Wyłącznie zdania NL — parser ustala trigger, typ raportu, format, odbiorcę
SCHEDULED_REPORT_QUERIES: tuple[str, ...] = (
    "Codziennie o 9:00 generuj raport sprzedaży PDF i wyślij email do team@firma.pl",
    "Co poniedziałek raport HR w xlsx i wyślij do hr@firma.pl",
    "Pierwszego każdego miesiąca raport finansów PDF do cfo@firma.pl",
    "Codziennie o 9:00 raport sprzedaży CSV i wyślij do manager@firma.pl",
)


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Przykład: Zaplanowane Raporty ===\n")

    if not ensure_services(client):
        return {}

    print("📋 Analiza zapytań (NLP → DSL, bez wykonania):\n")
    preview_text_examples(client, "", SCHEDULED_REPORT_QUERIES, finalize_artifacts=False)

    print("\n📋 Wykonywanie z rozpoznanego DSL (execute=true):\n")
    results: list[dict[str, Any]] = []
    for query in SCHEDULED_REPORT_QUERIES:
        result = execute_from_text(client, query, label="Harmonogram + raport")
        results.append(result)

    ok = sum(1 for r in results if r.get("status") == "executed")
    print(f"\n📊 Wykonano: {ok}/{len(SCHEDULED_REPORT_QUERIES)}")

    if ok == len(SCHEDULED_REPORT_QUERIES):
        print("\n🎉 Wszystkie zaplanowane raporty zostały utworzone!")
    else:
        print("\n⚠️  Część zapytań incomplete — sprawdź .nlp2dsl/pipeline/*.yaml")
        for r in results:
            if r.get("status") != "executed":
                print_workflow_preview(r)

    print("\n💡 W systemie produkcyjnym te workflow byłyby uruchamiane")
    print("   automatycznie według triggerów rozpoznanych z tekstu.")

    last = results[-1] if results else {}
    dsl = last.get("dsl") if isinstance(last.get("dsl"), dict) else None
    if not dsl or not dsl.get("steps"):
        plan = client.workflow_from_text(SCHEDULED_REPORT_QUERIES[0], execute=False, mode="rules")
        dsl = plan.get("dsl") if isinstance(plan.get("dsl"), dict) else None

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
        print("\n📦 Export markpact + pactown (publish layer):")
        bundle = export_workflow_publish_layer(
            artifact_root,
            dsl,
            catalog_from_nlp_client(client),
            source_query=SCHEDULED_REPORT_QUERIES[0],
            title=f"{dsl.get('name', 'workflow')} — scheduled report",
        )
        print_publish_summary(bundle, validation=validate_publish_layer(bundle))

    from nlp2dsl_artifacts import get_example_writer

    writer = get_example_writer()
    if writer:
        writer.finalize(client)

    return results[-1] if results else {}
