#!/usr/bin/env python3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
for p in (REPO_ROOT, EXAMPLE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scenario import run

if __name__ == "__main__":
    run()
