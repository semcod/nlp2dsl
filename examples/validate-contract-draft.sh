#!/usr/bin/env bash
# Wrapper — uruchamiaj z examples/ (NIE examples/scripts/).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/validate-contract-draft.sh" "$@"
