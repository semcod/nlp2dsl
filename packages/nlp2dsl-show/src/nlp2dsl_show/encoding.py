"""UTF-8 stdio for nlp2dsl-show CLI."""

from __future__ import annotations

import locale
import os
import sys


def configure_utf8() -> None:
    if os.environ.get("NLP2DSL_UTF8", "1").strip().lower() in {"0", "false", "no", "off"}:
        return
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    if not os.environ.get("LANG"):
        os.environ["LANG"] = "C.UTF-8"
    for loc in ("C.UTF-8", "en_US.UTF-8", "pl_PL.UTF-8"):
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except locale.Error:
            continue
