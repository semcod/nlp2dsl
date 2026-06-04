"""Backward-compat shim — use app.conversation.*."""

from app.conversation.merge import merge_into_state as _merge_into_state
from app.conversation.orchestrator import (
    _store,
    continue_conversation,
    get_conversation,
    start_conversation,
)
from app.conversation.responses import format_system_result as _format_system_result
from app.dsl.forms import get_action_form

__all__ = [
    "_format_system_result",
    "_merge_into_state",
    "_store",
    "continue_conversation",
    "get_action_form",
    "get_conversation",
    "start_conversation",
]
