"""Shared idempotent workflow execution helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import HTTPException

from app.engine import run_workflow
from app.idempotency import idempotency_store, workflow_fingerprint
from app.mullm_execute import execute_mullm_dsl
from app.workflow_lifecycle import run_request_from_workflow
from nlp2dsl_sdk.contracts.registry import SIDE_EFFECT_ACTIONS
from nlp2dsl_sdk.mullm.executor import is_mullm_only_workflow


def workflow_has_side_effects(workflow: Mapping[str, Any]) -> bool:
    """Return True when the workflow contains at least one side-effect action."""
    for step in workflow.get("steps") or []:
        if not isinstance(step, Mapping):
            continue
        action = str(step.get("action") or "")
        if action in SIDE_EFFECT_ACTIONS:
            return True
    return False


def derive_chat_idempotency_key(conversation_id: str, workflow: Mapping[str, Any]) -> str:
    """Stable idempotency key for repeated chat execute on the same planned DSL."""
    fingerprint = workflow_fingerprint(workflow)
    raw = f"chat:{conversation_id}:{fingerprint}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def resolve_idempotency_key(
    *,
    explicit_key: str | None,
    workflow: Mapping[str, Any],
    conversation_id: str | None = None,
) -> str | None:
    """Resolve an idempotency key from the request body or chat conversation context."""
    key = str(explicit_key or "").strip() or None
    if key:
        return key
    if conversation_id and workflow_has_side_effects(workflow):
        return derive_chat_idempotency_key(conversation_id, workflow)
    return None


async def run_idempotent_workflow(
    workflow: Mapping[str, Any],
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """
    Execute a workflow once, optionally deduplicating by idempotency key.

    Returns:
        {
            "result": <WorkflowResult dict>,
            "idempotency_key": str | None,
            "idempotent_replay": bool,
        }
    """
    key = str(idempotency_key or "").strip() or None
    if key:
        start_status, cached_response = await idempotency_store.start(
            key,
            workflow_fingerprint(workflow),
        )
        if start_status == "conflict":
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail={
                    "error": "idempotency_key_conflict",
                    "idempotency_key": key,
                    "message": "Ten idempotency_key został użyty z innym workflow.",
                },
            )
        if start_status == "in_progress":
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail={
                    "error": "idempotency_key_in_progress",
                    "idempotency_key": key,
                    "message": "Wykonanie z tym idempotency_key jest już w toku.",
                },
            )
        if start_status == "replay" and cached_response is not None:
            replay = dict(cached_response)
            replay["idempotent_replay"] = True
            replay.setdefault("idempotency_key", key)
            return replay

    if is_mullm_only_workflow(dict(workflow)):
        mullm_result = await execute_mullm_dsl(dict(workflow))
        payload = {
            "result": mullm_result,
            "idempotency_key": key,
            "idempotent_replay": False,
        }
    else:
        wf_result = await run_workflow(run_request_from_workflow(workflow))
        payload = {
            "result": wf_result.model_dump(mode="json"),
            "idempotency_key": key,
            "idempotent_replay": False,
        }
    if key:
        await idempotency_store.finish(key, payload)
    return payload
