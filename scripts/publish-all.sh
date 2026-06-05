#!/usr/bin/env bash
# Build and upload all nlp2dsl packages + root SDK to PyPI (dependency order).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"

PACKAGES=(
  "$ROOT/packages/pact-ir"
  "$ROOT/packages/nlp2cmd-intent"
  "$ROOT/packages/nlp2cmd-planner"
  "$ROOT/packages/nlp2cmd-propact"
  "$ROOT/packages/nlp2dsl-show"
)

require_tool() {
  "$PY" -c "import $1" 2>/dev/null || {
    echo "Missing Python package: $1 (pip install build twine)" >&2
    exit 1
  }
}

require_tool build
require_tool twine

echo "==> Build root SDK (nlp2dsl)"
"$PY" -m build "$ROOT"

for pkg in "${PACKAGES[@]}"; do
  name="$(basename "$pkg")"
  echo "==> Build $name"
  "$PY" -m build "$pkg"
done

echo "==> Upload root SDK"
"$PY" -m twine upload "$ROOT"/dist/*

for pkg in "${PACKAGES[@]}"; do
  name="$(basename "$pkg")"
  echo "==> Upload $name"
  "$PY" -m twine upload "$pkg"/dist/*
done

echo "Done. Published nlp2dsl + ${#PACKAGES[@]} packages."
