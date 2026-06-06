"""Shared publish-layer export (markpact + pactown) for examples and artifacts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from nlp2dsl_sdk.contracts import action_catalog_payload, contract_from_registry_entry

from .markpact import MarkpactExportBundle, export_markpact_bundle
from .pactown import PactownExportBundle, export_pactown_bundle

DEFAULT_BACKEND_URL = "http://localhost:8010"

_FALLBACK_CONTRACTS = {
    "generate_report": contract_from_registry_entry(
        "generate_report",
        {
            "description": "Generuje raport",
            "required": ["report_type"],
            "optional": {"format": "pdf"},
        },
    ),
    "send_email": contract_from_registry_entry(
        "send_email",
        {
            "description": "Wysyła e-mail",
            "required": ["to", "subject", "body"],
            "quality_required": ["body"],
        },
    ),
    "send_invoice": contract_from_registry_entry(
        "send_invoice",
        {
            "description": "Wysyła fakturę",
            "required": ["amount", "to"],
            "optional": {"currency": "PLN"},
        },
    ),
    "notify_slack": contract_from_registry_entry(
        "notify_slack",
        {
            "description": "Powiadomienie Slack",
            "optional": {"channel": "#general", "message": ""},
            "quality_required": ["message"],
        },
    ),
}


@dataclass
class PublishExportBundle:
    markpact: MarkpactExportBundle
    pactown: PactownExportBundle


def catalog_from_nlp_client(client: Any | None) -> dict[str, Any]:
    """Fetch /nlp/actions or return minimal fallback catalog."""
    if client is not None:
        try:
            resp = client._nlp_service("GET", "/nlp/actions")
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and payload:
                return payload
        except Exception:
            pass
    return action_catalog_payload(_FALLBACK_CONTRACTS)


def export_workflow_publish_layer(
    artifact_root: Path | str,
    dsl: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    source_query: str = "",
    title: str | None = None,
    backend_url: str | None = None,
) -> PublishExportBundle:
    """Write markpact + pactown trees under artifact_root/generated/."""
    root = Path(artifact_root)
    backend = backend_url or os.environ.get("NLP2DSL_BACKEND_URL", DEFAULT_BACKEND_URL)
    markpact = export_markpact_bundle(
        root / "generated" / "markpact",
        dsl,
        catalog,
        title=title,
        backend_url=backend,
        source_query=source_query,
    )
    pactown = export_pactown_bundle(
        root / "generated" / "pactown",
        markpact_readme=markpact.readme,
    )
    return PublishExportBundle(markpact=markpact, pactown=pactown)


def validate_publish_layer(bundle: PublishExportBundle) -> dict[str, str]:
    """Optional validation when markpact/pactown are installed."""
    report: dict[str, str] = {}
    try:
        from markpact.parser import parse_blocks

        n = len(parse_blocks(bundle.markpact.readme.read_text(encoding="utf-8")))
        report["markpact"] = f"{n} blocks OK"
    except ImportError:
        report["markpact"] = "skipped (markpact not installed)"
    except Exception as exc:
        report["markpact"] = f"error: {exc}"

    try:
        from pactown.config import load_config

        cfg = load_config(bundle.pactown.ecosystem_yaml)
        report["pactown"] = f"{cfg.name}: {len(cfg.services)} services OK"
    except ImportError:
        report["pactown"] = "skipped (pactown not installed)"
    except Exception as exc:
        report["pactown"] = f"error: {exc}"

    return report


def print_publish_summary(bundle: PublishExportBundle, *, validation: Mapping[str, str] | None = None) -> None:
    print("✅ Export markpact + pactown:")
    print(f"   markpact README: {bundle.markpact.readme}")
    print(f"   pactown ecosystem: {bundle.pactown.ecosystem_yaml}")
    if validation:
        for key, msg in validation.items():
            icon = "🔍" if "OK" in msg else "💡" if "skipped" in msg else "⚠️"
            print(f"   {icon} {key}: {msg}")
