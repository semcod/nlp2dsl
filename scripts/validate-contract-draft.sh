#!/usr/bin/env bash
# Walidacja draftów kontraktów — uruchamiaj z repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/_ensure_nlp2dsl_sdk.sh
source "$ROOT/scripts/_ensure_nlp2dsl_sdk.sh"
PY="$(ensure_nlp2dsl_sdk "$ROOT")"
exec "$PY" "$ROOT/scripts/validate-contract-draft.py" "$@"
