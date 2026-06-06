"""Example: export pactown bundle and produce deploy instructions."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.deploy.pactown_deploy import deploy_instructions, validate_pactown_bundle
from workflow_export.publish import (
    catalog_from_nlp_client,
    export_workflow_publish_layer,
    validate_publish_layer,
)
from nlp2dsl_sdk.preview import ensure_services

SOURCE_QUERY = "Raport sprzedaży PDF i wyślij email do manager@firma.pl"


def _dsl_from_client(client: NLP2DSLClient) -> dict[str, Any]:
    result = client.workflow_from_text(SOURCE_QUERY, execute=False, mode="rules")
    dsl = result.get("dsl") or result.get("workflow")
    if isinstance(dsl, dict) and dsl.get("steps"):
        return dsl
    return {
        "name": "report_and_email",
        "trigger": "daily",
        "steps": [
            {"action": "generate_report", "config": {"report_type": "sales", "format": "pdf"}},
            {
                "action": "send_email",
                "config": {
                    "to": "manager@firma.pl",
                    "subject": "Raport sprzedaży",
                    "body": "Automatyczny raport.",
                },
            },
        ],
    }


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    example_dir = Path(os.environ.get("NLP2DSL_EXAMPLE_DIR", ".")).resolve()
    artifact_root = example_dir / ".nlp2dsl"

    print("=== 20-pactown-deploy ===\n")

    if not ensure_services(client):
        print("⚠️  Platforma niedostępna — export z fallback DSL\n")

    catalog = catalog_from_nlp_client(client)
    dsl = _dsl_from_client(client)

    bundle = export_workflow_publish_layer(
        artifact_root,
        dsl,
        catalog,
        source_query=SOURCE_QUERY,
        title="report_and_email — pactown deploy",
    )
    publish_validation = validate_publish_layer(bundle)
    pactown_validation = validate_pactown_bundle(bundle.pactown.root)
    deploy = deploy_instructions(repo_root=REPO_ROOT, pactown_dir=bundle.pactown.root)

    print("📦 Pactown export:", bundle.pactown.ecosystem_yaml)
    print("   publish valid:", publish_validation.get("valid", publish_validation))
    print("   pactown valid:", pactown_validation["valid"])
    if pactown_validation.get("issues"):
        for issue in pactown_validation["issues"]:
            print(f"   ⚠️  {issue}")
    print("   pactown CLI:", pactown_validation.get("pactown_cli_detail"))

    print("\n🚀 Deploy steps:")
    for step in deploy["steps"]:
        print(f"   {step}")
    print("\n🏥 Health checks:")
    for cmd in deploy["health_checks"]:
        print(f"   {cmd}")

    out = artifact_root / "deploy" / "instructions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(deploy, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Zapisano: {out.relative_to(example_dir)}")

    assert pactown_validation["valid"], f"Pactown bundle invalid: {pactown_validation['issues']}"
    return deploy


if __name__ == "__main__":
    run()
