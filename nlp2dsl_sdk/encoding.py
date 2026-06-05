"""UTF-8 stdio setup — fixes broken Polish output (znajdź → znajd?) on ASCII locales."""

from __future__ import annotations

import locale
import os
import sys


def configure_utf8(*, force: bool = False) -> None:
    """
    Reconfigure stdout/stderr to UTF-8 and prefer UTF-8 locale.

    Call at CLI entry (main) before any print with Polish text or emoji.
    Disable with NLP2DSL_UTF8=0.
    """
    if not force and os.environ.get("NLP2DSL_UTF8", "1").strip().lower() in {"0", "false", "no", "off"}:
        return

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if not os.environ.get("LANG"):
        os.environ["LANG"] = "C.UTF-8"
    if not os.environ.get("LC_ALL"):
        os.environ["LC_ALL"] = os.environ.get("LANG", "C.UTF-8")
    if not os.environ.get("LC_CTYPE"):
        os.environ["LC_CTYPE"] = os.environ.get("LANG", "C.UTF-8")

    for loc in ("C.UTF-8", "en_US.UTF-8", "pl_PL.UTF-8"):
        try:
            locale.setlocale(locale.LC_ALL, loc)
            break
        except locale.Error:
            continue


def utf8_open(path, mode="r", **kwargs):
    """open() with UTF-8 default encoding."""
    if "encoding" not in kwargs and "b" not in mode:
        kwargs["encoding"] = "utf-8"
    return open(path, mode, **kwargs)
