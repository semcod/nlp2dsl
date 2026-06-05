#!/usr/bin/env python3
"""Benchmark 20 zapytań — różne obiekty (invoice, slack, crm, code, …)."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXAMPLE_DIR = Path(__file__).resolve().parent
if str(EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_DIR))

from scenario import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark multi-object NLP2DSL")
    parser.add_argument(
        "--modes",
        default="rules,auto",
        help="Tryby parsera po przecinku (rules, auto, llm)",
    )
    args = parser.parse_args()
    modes = tuple(m.strip() for m in args.modes.split(",") if m.strip())
    run(modes=modes)


if __name__ == "__main__":
    main()
