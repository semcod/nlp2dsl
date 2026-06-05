"""
Conversation Orchestrator — stanowy dialog AI → DSL.

Pipeline: resolve_intent → merge → unknown → system → DSL → incomplete.
"""

import logging
from uuid import uuid4

from app.conversation.merge import merge_into_state
from app.conversation.responses import (
    build_and_check_dsl,
    build_incomplete_response,
    check_execute_keyword,
    deny_message,
    handle_system_action,
    handle_unknown_intent,
)
from app.routing import IntentDecision, resolve_intent
from app.schemas import ConversationResponse, ConversationState
from app.store.factory import get_conversation_store

log = logging.getLogger("orchestrator")

_store = get_conversation_store()

_CONVERSATION_ID_LENGTH: int = int("12")


async def start_conversation(text: str) -> ConversationResponse:
    state = ConversationState(id=uuid4().hex[:_CONVERSATION_ID_LENGTH])
    state.history.append({"role": "user", "text": text})
    result = await _process_message(state, text)
    await _store.save(state.id, state.model_dump())
    return result


async def continue_conversation(conversation_id: str, text: str) -> ConversationResponse:
    raw = await _store.get(conversation_id)
    if not raw:
        log.info("Conversation %s not found; creating new state lazily", conversation_id)
        state = ConversationState(id=conversation_id)
    else:
        state = ConversationState(**raw)

    state.history.append({"role": "user", "text": text})
    result = await _process_message(state, text)
    await _store.save(state.id, state.model_dump())
    return result


async def get_conversation(conversation_id: str) -> ConversationState | None:
    raw = await _store.get(conversation_id)
    if raw:
        return ConversationState(**raw)
    return None


def _attach_routing(
    resp: ConversationResponse,
    decision: IntentDecision,
) -> ConversationResponse:
    resp.routing = decision.to_dict()
    return resp


async def _process_message(state: ConversationState, text: str) -> ConversationResponse:
    execute_response = await check_execute_keyword(state, text)
    if execute_response:
        return execute_response

    decision, nlp = await resolve_intent(text)
    log.info(
        "Intent: action=%s source=%s conf=%.2f authorized=%s",
        decision.action,
        decision.source,
        decision.confidence,
        decision.authorized,
    )

    if nlp is None:
        msg = deny_message(decision)
        state.history.append({"role": "assistant", "text": msg})
        return _attach_routing(
            ConversationResponse(
                conversation_id=state.id,
                status="in_progress",
                message=msg,
            ),
            decision,
        )

    merge_into_state(state, nlp)

    unknown_response = handle_unknown_intent(state)
    if unknown_response:
        return _attach_routing(unknown_response, decision)

    system_response = handle_system_action(state)
    if system_response:
        return _attach_routing(system_response, decision)

    dsl_response = await build_and_check_dsl(state)
    if dsl_response:
        return _attach_routing(dsl_response, decision)

    return _attach_routing(await build_incomplete_response(state), decision)
