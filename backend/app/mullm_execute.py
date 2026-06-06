"""Async Mullm delegate execution for backend routes."""

from __future__ import annotations

import asyncio
from typing import Any

from nlp2dsl_sdk.mullm.executor import execute_mullm_workflow


async def execute_mullm_dsl(
    dsl: dict[str, Any],
    *,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Run Mullm-only DSL via orchestrator API (thread offload for sync HTTP)."""
    return await asyncio.to_thread(
        execute_mullm_workflow,
        dsl,
        session_id=conversation_id,
    )
