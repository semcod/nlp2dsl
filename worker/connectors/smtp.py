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
        return cls(
            host=host,
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER", "").strip(),
            password=os.getenv("SMTP_PASSWORD", "").strip(),
            use_tls=os.getenv("SMTP_TLS", "1").strip().lower() not in {"0", "false", "no"},
            from_addr=os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "nlp2dsl@localhost")).strip(),
            timeout=float(os.getenv("SMTP_TIMEOUT", "30")),
        )


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

    with smtplib.SMTP(cfg.host, cfg.port, timeout=cfg.timeout) as smtp:
        if cfg.use_tls:
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
