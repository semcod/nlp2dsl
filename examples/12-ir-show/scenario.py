"""Porównanie: MVP workflow (nlp-service) vs IntentIR (nlp2dsl show)."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient
from nlp2dsl_sdk.encoding import configure_utf8
from nlp2dsl_sdk.preview import ensure_services, print_json, print_workflow_preview

IR_QUERIES: tuple[str, ...] = (
    "znajdź pliki *.py w src",
    "uruchom testy jednostkowe",
    "pokaż status systemu",
)

MVP_QUERIES: tuple[str, ...] = (
    "Wyślij fakturę na 500 PLN do test@firma.pl",
    "Powiadom #devops: backup gotowy",
)


def _run_show(query: str, *, with_plan: bool = False) -> dict[str, Any] | None:
    exe = shutil.which("nlp2dsl-show") or shutil.which("nlp2dsl")
    if not exe:
        return None
    cmd = [exe, "show", query]
    if with_plan:
        cmd.append("--plan")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except (subprocess.TimeoutExpired, OSError):
        return {"error": "timeout or spawn failed"}
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or proc.stdout.strip(), "exit_code": proc.returncode}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw": proc.stdout.strip()}


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    configure_utf8(force=True)
    client = client or NLP2DSLClient.from_env()
    print("=== MVP (Docker workflow) vs IR (nlp2dsl show) ===\n")

    out: dict[str, Any] = {"mvp": [], "ir": []}

    if ensure_services(client):
        print("--- MVP: /workflow/from-text ---")
        for text in MVP_QUERIES:
            print(f"\n📝 {text}")
            result = client.workflow_from_text(text, mode="auto")
            out["mvp"].append(result)
            print_workflow_preview(result)
    else:
        print("⚠️  MVP offline — pomijam workflow/from-text")

    print("\n--- IR: nlp2dsl show (shell/IntentIR, nie Docker worker) ---")
    if not (shutil.which("nlp2dsl-show") or shutil.which("nlp2dsl")):
        print("ℹ️  Zainstaluj: pip install -e . && ./scripts/setup-dev.sh")
        print("   Intract gate: NLP2CMD_INTRACT_GATE=1 nlp2dsl show 'query' --plan")
        return out

    for text in IR_QUERIES:
        print(f"\n🔍 show: {text}")
        payload = _run_show(text)
        out["ir"].append({"query": text, "result": payload})
        if payload:
            print_json(payload)

    return out
