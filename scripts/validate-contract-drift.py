#!/usr/bin/env python3
"""CI gate: nlp-service registry vs worker handlers vs backend fallback catalog."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NLP_SERVICE = ROOT / "nlp-service"
WORKER = ROOT / "worker"
BACKEND = ROOT / "backend"


def _nlp_catalog() -> dict:
    saved = sys.path[:]
    try:
        if str(NLP_SERVICE) not in sys.path:
            sys.path.insert(0, str(NLP_SERVICE))
        from app.registry import ACTIONS_REGISTRY
        from dsl_contracts import action_catalog_payload, contract_from_registry_entry

        contracts = {
            name: contract_from_registry_entry(name, meta)
            for name, meta in ACTIONS_REGISTRY.items()
        }
        return action_catalog_payload(contracts)
    finally:
        sys.path[:] = saved


def _worker_handlers() -> list[str]:
    saved = sys.path[:]
    try:
        if str(WORKER) not in sys.path:
            sys.path.insert(0, str(WORKER))
        import worker as worker_mod

        return sorted(worker_mod.ACTION_HANDLERS)
    finally:
        sys.path[:] = saved


def _backend_fallback_catalog() -> dict:
    from dsl_contracts import action_catalog_payload, contract_from_registry_entry

    saved = sys.path[:]
    try:
        # Isolate backend imports from nlp-service `app` package.
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]
        if str(BACKEND) not in sys.path:
            sys.path.insert(0, str(BACKEND))
        catalog_mod = importlib.import_module("app.action_catalog")
        contracts = {
            name: contract_from_registry_entry(name, meta)
            for name, meta in catalog_mod._FALLBACK_ACTION_FIELDS.items()
        }
        return action_catalog_payload(contracts)
    finally:
        sys.path[:] = saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument(
        "--check-backend-fallback",
        action="store_true",
        help="Also compare nlp-service vs backend offline fallback catalog",
    )
    args = parser.parse_args()

    from dsl_validate.contract_drift import build_catalog_drift_report

    backend_catalog = _backend_fallback_catalog() if args.check_backend_fallback else None
    report = build_catalog_drift_report(
        nlp_catalog=_nlp_catalog(),
        worker_handlers=_worker_handlers(),
        backend_catalog=backend_catalog,
    )

    if args.json:
        import json

        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        if report.ok:
            print("OK: action catalog drift — no issues")
        else:
            print(f"FAIL: action catalog drift — {len(report.issues)} issue(s)", file=sys.stderr)
            for issue in report.issues:
                print(f"  - [{issue.code}] {issue.message}", file=sys.stderr)

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
