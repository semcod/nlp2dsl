"""Attachment requirement checks for send_invoice workflows."""

from __future__ import annotations

from app.conversation.invoice_policy import invoice_attachment_policy_active
from app.conversation.doql_context import DoqlTaskContext
from app.schemas import ConversationState, DialogResponse


def workflow_needs_attachment(
    state: ConversationState,
    dialog: DialogResponse,
    ctx: DoqlTaskContext | None = None,
) -> bool:
    if ctx is not None and not invoice_attachment_policy_active(ctx, state):
        return False
    if ctx is None and not state.attachment_required:
        return False
    workflow = dialog.workflow
    if not workflow:
        return True
    for step in workflow.steps:
        if step.action == "send_invoice":
            return not str(step.config.get("attachment_path", "")).strip()
    return False
