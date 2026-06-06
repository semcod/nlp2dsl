"""Scenariusz: export ActionContract + DSL → markpact README + pactown ecosystem."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.export.publish import (
    catalog_from_nlp_client,
    export_workflow_publish_layer,
    print_publish_summary,
    validate_publish_layer,
)
from nlp2dsl_sdk.preview import ensure_services

SOURCE_QUERY = (
    "Codziennie o 9:00 raport sprzedaży PDF i wyślij email do manager@firma.pl"
)


def _dsl_from_client(client: NLP2DSLClient) -> dict[str, Any]:
    result = client.workflow_from_text(SOURCE_QUERY, execute=False, mode="rules")
    dsl = result.get("dsl")
    if isinstance(dsl, dict) and dsl.get("steps"):
        return dsl
    return {
        "name": "report_and_email",
        "trigger": "daily",
        "steps": [
            {
                "action": "generate_report",
                "config": {"report_type": "sales", "format": "pdf"},
            },
            {
                "action": "send_email",
                "config": {
                    "to": "manager@firma.pl",
                    "subject": "Automatyczna wiadomość",
                    "body": "W załączeniu przesyłamy raport sales.",
                },
            },
        ],
    }


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    example_dir = Path(os.environ.get("NLP2DSL_EXAMPLE_DIR", ".")).resolve()
    artifact_root = example_dir / ".nlp2dsl"

    print("=== Przykład: Export markpact + pactown (report_and_email) ===\n")

    if not ensure_services(client):
        print("⚠️  Platforma niedostępna — export z fallback DSL/katalogiem\n")

    catalog = catalog_from_nlp_client(client)
    dsl = _dsl_from_client(client)

    print("📋 DSL do eksportu:")
    print(json.dumps(dsl, indent=2, ensure_ascii=False))
    print()

    bundle = export_workflow_publish_layer(
        artifact_root,
        dsl,
        catalog,
        source_query=SOURCE_QUERY,
        title="report_and_email — scheduled sales report",
    )
    validation = validate_publish_layer(bundle)
    print_publish_summary(bundle, validation=validation)

    print()
    print("💡 Następne kroki:")
    print(f"   cd {bundle.pactown.root} && pactown validate nlp2dsl-platform.pactown.yaml")
    print(f"   markpact --test {bundle.markpact.readme}  # gdy backend działa")
    print()

    from nlp2dsl_sdk.artifacts import get_example_writer

    writer = get_example_writer()
    if writer:
        writer.record(
            SOURCE_QUERY,
            {
                "status": "exported",
                "dsl": dsl,
                "markpact_readme": str(bundle.markpact.readme),
                "pactown_ecosystem": str(bundle.pactown.ecosystem_yaml),
            },
            mode="export",
        )
        writer.finalize(client)

    return {
        "status": "exported",
        "dsl": dsl,
        "markpact_readme": str(bundle.markpact.readme),
        "pactown_ecosystem": str(bundle.pactown.ecosystem_yaml),
    }
