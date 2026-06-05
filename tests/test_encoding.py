"""Tests for UTF-8 stdio configuration."""

import io
import sys

from nlp2dsl_sdk.encoding import configure_utf8


def test_configure_utf8_reconfigures_stdout(monkeypatch):
    buf = io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict")
    monkeypatch.setattr(sys, "stdout", buf)
    configure_utf8(force=True)
    assert sys.stdout.encoding.lower().replace("-", "") == "utf8"


def test_configure_utf8_respects_disable(monkeypatch):
    monkeypatch.setenv("NLP2DSL_UTF8", "0")
    buf = io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict")
    monkeypatch.setattr(sys, "stdout", buf)
    configure_utf8()
    assert sys.stdout.encoding.lower() == "ascii"
