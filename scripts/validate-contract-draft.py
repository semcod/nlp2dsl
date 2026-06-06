#!/usr/bin/env python3
"""Validate LLM-generated contract drafts under .nlp2dsl/generated/contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from nlp2dsl_sdk.contracts.draft import (  # noqa: E402
        list_draft_files,
        load_draft,
        validate_draft,
    )
except ModuleNotFoundError as exc:
    if exc.name in {"pydantic", "yaml"}:
        print(
            "Brak zależności SDK. Uruchom z repo root:\n"
            "  pip install -e .\n"
            "lub:\n"
            "  bash scripts/validate-contract-draft.sh --strict",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repo root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any draft has validation issues",
    )
    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Fail when drafts are not approved/active",
    )
    args = parser.parse_args()

    files = list_draft_files(root=args.root)
    if not files:
        print("OK — no draft files")
        return 0

    errors = 0
    for path in files:
        draft = load_draft(path)
        issues = validate_draft(draft)
        rel = path.relative_to(args.root)
        if issues:
            errors += 1
            print(f"FAIL {rel} status={draft.status}")
            for issue in issues:
                print(f"  • {issue.code}: {issue.to_legacy_message()}")
            continue
        if args.require_approved and draft.status not in {"approved", "active"}:
            errors += 1
            print(f"FAIL {rel} status={draft.status} (not approved/active)")
            continue
        print(f"OK   {rel} status={draft.status} name={draft.name}")

    if errors and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
