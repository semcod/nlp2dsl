#!/usr/bin/env python3
"""Konwersacyjny flow — demo skryptowane lub tryb interaktywny (-i)."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scenario import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Przykład konwersacyjnego flow")
    parser.add_argument("--interactive", "-i", action="store_true", help="Tryb interaktywny")
    args = parser.parse_args()
    run(interactive=args.interactive)


if __name__ == "__main__":
    main()
