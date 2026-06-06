"""Tests for SMTP connector."""

from __future__ import annotations

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from connectors.smtp import SmtpConfig, send_smtp_message


def test_smtp_config_from_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SMTP_HOST", raising=False)
    assert SmtpConfig.from_env() is None


def test_smtp_config_from_env_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "mailhog")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_TLS", "0")
    cfg = SmtpConfig.from_env()
    assert cfg is not None
    assert cfg.host == "mailhog"
    assert cfg.port == 1025
    assert cfg.use_tls is False


def test_send_smtp_message_without_config_raises() -> None:
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        send_smtp_message(to="a@b.pl", subject="Hi", body="Test", config=None)


def test_send_smtp_message_calls_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = SmtpConfig(host="localhost", port=1025, use_tls=False, from_addr="test@local")
    sent: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float = 30) -> None:
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self) -> None:
            pass

        def login(self, user: str, password: str) -> None:
            pass

        def send_message(self, message: EmailMessage) -> None:
            sent.append(message)

    monkeypatch.setattr("connectors.smtp.smtplib.SMTP", FakeSMTP)
    result = send_smtp_message(
        to="client@firma.pl",
        subject="Faktura",
        body="Załącznik w załączeniu.",
        config=cfg,
    )
    assert result["transport"] == "smtp"
    assert result["sent_to"] == "client@firma.pl"
    assert len(sent) == 1
    assert sent[0]["To"] == "client@firma.pl"
