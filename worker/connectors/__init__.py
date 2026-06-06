"""External service connectors for worker actions."""

try:
    from worker.connectors.smtp import SmtpConfig, send_smtp_message
except ImportError:
    from connectors.smtp import SmtpConfig, send_smtp_message

__all__ = ["SmtpConfig", "send_smtp_message"]
