#!/usr/bin/env python3
"""Validate markpact/pactown export for canonical workflow DSL fixtures."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nlp2dsl_sdk.contracts import action_catalog_payload, contract_from_registry_entry
from nlp2dsl_sdk.export.publish import (
    assert_publish_layer_valid,
    export_workflow_publish_layer,
    validate_publish_layer_result,
)

_CANONICAL_DSLS: tuple[tuple[str, dict], ...] = (
    (
        "report_and_email",
        {
            "name": "report_and_email",
            "trigger": "daily",
            "steps": [
                {"action": "generate_report", "config": {"report_type": "sales", "format": "pdf"}},
                {
                    "action": "send_email",
                    "config": {"to": "team@firma.pl", "subject": "Raport", "body": "Załącznik."},
                },
            ],
        },
    ),
    (
        "full_report_flow",
        {
            "name": "full_report_flow",
            "trigger": "weekly",
            "steps": [
                {"action": "generate_report", "config": {"report_type": "sales", "format": "pdf"}},
                {
                    "action": "send_email",
                    "config": {"to": "manager@firma.pl", "subject": "Raport", "body": "Załącznik."},
                },
                {"action": "notify_slack", "config": {"channel": "#sales", "message": "Raport gotowy."}},
            ],
        },
    ),
)


def _sample_catalog() -> dict:
    return action_catalog_payload(
        {
            "generate_report": contract_from_registry_entry(
                "generate_report", {"required": ["report_type"], "optional": {"format": "pdf"}}
            ),
            "send_email": contract_from_registry_entry(
                "send_email", {"required": ["to", "subject", "body"], "quality_required": ["body"]}
            ),
            "notify_slack": contract_from_registry_entry(
                "notify_slack", {"optional": {"channel": "#general"}, "quality_required": ["message"]}
            ),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require markpact and pactown packages (fail if missing)",
    )
    args = parser.parse_args()

    catalog = _sample_catalog()
    failures = 0

    with tempfile.TemporaryDirectory(prefix="nlp2dsl-publish-") as tmp:
        root = Path(tmp)
        for name, dsl in _CANONICAL_DSLS:
            bundle = export_workflow_publish_layer(root / name, dsl, catalog, source_query=name)
            if args.strict:
                try:
                    assert_publish_layer_valid(bundle, require_packages=True)
                    print(f"OK: {name} — publish layer validated")
                except ValueError as exc:
                    failures += 1
                    print(f"FAIL: {name} — {exc}", file=sys.stderr)
            else:
                result = validate_publish_layer_result(bundle)
                print(f"{'OK' if result.ok or result.skipped else 'FAIL'}: {name} — {result.to_dict()}")
                if not result.ok and not result.skipped:
                    failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
