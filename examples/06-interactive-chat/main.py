#!/usr/bin/env python3
"""Interaktywny chat z NLP2DSL w terminalu."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenario import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Interaktywny chat z NLP2DSL")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Pełny tryb interaktywny (domyślnie: krótkie demo skryptowane)",
    )
    args = parser.parse_args()
    run(interactive=args.interactive)


if __name__ == "__main__":
    main()
