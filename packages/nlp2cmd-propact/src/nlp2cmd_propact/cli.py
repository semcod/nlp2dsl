"""Deprecated: use nlp2dsl show (structure) and nlp2cmd plan (execution)."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    del argv
    print(
        "nlp2dsl-run is deprecated.\n\n"
        "  nlp2dsl show 'QUERY'              # IntentIR / query structure (no execution)\n"
        "  nlp2cmd plan 'QUERY'              # plan → Propact markdown\n"
        "  nlp2cmd plan 'QUERY' --execute    # run via Propact\n"
        "  nlp2cmd -q 'QUERY' -r             # legacy runtime (browser/canvas/shell)\n",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
