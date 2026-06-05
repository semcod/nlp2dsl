"""Invoice attachment policy — generate or ask; never skip silently."""

from __future__ import annotations

from app.conversation.doql_context import DoqlTaskContext
from app.schemas import ConversationState


def is_invoice_example(name: str) -> bool:
    return "invoice" in (name or "").lower()


def invoice_attachment_policy_active(
    ctx: DoqlTaskContext,
    state: ConversationState | None = None,
    *,
    intent: str | None = None,
) -> bool:
    """True when send_invoice must resolve attachment (fixture, generate, or ask user)."""
    if ctx.attachment_required:
        return True
    if state is not None and state.attachment_required:
        return True
    resolved_intent = intent or (state.intent if state else None) or ""
    if resolved_intent == "send_invoice" or is_invoice_example(ctx.example_name):
        return bool(ctx.generate_invoice_if_missing)
    return False
