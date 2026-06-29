"""SMTP connector — real email delivery when SMTP_HOST is configured."""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int = 587
    user: str = ""
    password: str = ""
    use_tls: bool = True
    from_addr: str = ""
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> SmtpConfig | None:
        host = os.getenv("SMTP_HOST", "").strip()
        if not host:
            return None
        port = int(os.getenv("SMTP_PORT", "587"))
        tls_raw = os.getenv("SMTP_TLS", "1").strip().lower()
        use_tls = tls_raw not in {"0", "false", "no", "ssl", "smtps"}
        return cls(
            host=host,
            port=port,
            user=os.getenv("SMTP_USER", "").strip(),
            password=os.getenv("SMTP_PASSWORD", "").strip(),
            use_tls=use_tls,
            from_addr=os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "nlp2dsl@localhost")).strip(),
            timeout=float(os.getenv("SMTP_TIMEOUT", "30")),
        )


def _use_smtp_ssl(cfg: SmtpConfig) -> bool:
    tls_raw = os.getenv("SMTP_TLS", "1").strip().lower()
    if tls_raw in {"ssl", "smtps"}:
        return True
    if os.getenv("SMTP_SSL", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return cfg.port == 465


def send_smtp_message(
    *,
    to: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    config: SmtpConfig | None = None,
) -> dict[str, Any]:
    """Send email via SMTP. Raises on delivery failure."""
    cfg = config or SmtpConfig.from_env()
    if cfg is None:
        raise RuntimeError("SMTP_HOST not configured")

    message = EmailMessage()
    message["Subject"] = subject or "Automatyczna wiadomość"
    message["From"] = cfg.from_addr
    message["To"] = to
    message.set_content(body or "")

    if attachment_path:
        path = Path(attachment_path)
        if path.is_file():
            data = path.read_bytes()
            message.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=path.name,
            )

    if _use_smtp_ssl(cfg):
        smtp_ctx = smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=cfg.timeout)
    else:
        smtp_ctx = smtplib.SMTP(cfg.host, cfg.port, timeout=cfg.timeout)

    with smtp_ctx as smtp:
        if not _use_smtp_ssl(cfg) and cfg.use_tls:
            smtp.starttls()
        if cfg.user:
            smtp.login(cfg.user, cfg.password)
        smtp.send_message(message)

    return {
        "sent_to": to,
        "subject": subject,
        "transport": "smtp",
        "smtp_host": cfg.host,
        "attachment": attachment_path or None,
    }
