"""Backend execution policy adapter tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.execution_policy import (
    build_policy_context,
    policy_blocked_response,
    validate_workflow_execution_policy,
)


def test_build_policy_context_reads_nested_policy_block() -> None:
    ctx = build_policy_context(
        {
            "agent_id": "ops_agent",
            "approval_grants": ["send_email"],
            "policy": {
                "allowed_email_domains": ["company.com"],
                "allowed_notify_channels": ["#alerts"],
            },
        },
        executing=True,
    )
    assert ctx.agent_id == "ops_agent"
    assert "send_email" in ctx.approval_grants
    assert "company.com" in ctx.allowed_email_domains
    assert "#alerts" in ctx.allowed_notify_channels


@pytest.mark.asyncio
async def test_validate_workflow_execution_policy_blocks_without_access() -> None:
    workflow = {
        "steps": [{"action": "mullm_shell_task", "config": {"shell_command": "ls"}}],
    }
    body = {"agent_id": "mail_agent", "skip_access_check": True}
    with patch(
        "app.execution_policy.load_action_field_catalog",
        return_value={
            "mullm_shell_task": {
                "required": ["shell_command"],
                "category": "mullm",
                "execution": "delegate",
                "resource_area": "mullm:rag",
                "side_effect": True,
            }
        },
    ):
        ctx_issues = await validate_workflow_execution_policy(
            workflow,
            {
                **body,
                "process": {"access": {"deny_resource_areas": ["mullm:rag"]}},
            },
            executing=True,
            skip_access_check=True,
        )
    assert any(issue.code == "policy.scope_denied" for issue in ctx_issues)


@pytest.mark.asyncio
async def test_validate_workflow_execution_policy_uses_access_check() -> None:
    workflow = {"steps": [{"action": "send_email", "config": {"to": "a@b.c", "body": "x"}}]}
    with patch(
        "app.execution_policy.load_action_field_catalog",
        return_value={
            "send_email": {
                "required": ["to"],
                "quality_required": ["body"],
                "side_effect": True,
            }
        },
    ), patch(
        "app.execution_policy.fetch_access_decisions",
        AsyncMock(
            return_value={
                "send_email": {
                    "allowed": False,
                    "effect": "approval",
                    "reason": "requires_approval",
                }
            }
        ),
    ):
        issues = await validate_workflow_execution_policy(
            workflow,
            {"agent_id": "mail_agent"},
            executing=True,
        )
    assert any(issue.code == "policy.access_denied" for issue in issues)


def test_policy_blocked_response_shape() -> None:
    from nlp2dsl_sdk.validation.issue import ValidationIssue

    issues = [
        ValidationIssue(
            code="policy.approval_required",
            field_name="steps.0",
            message="needs approval",
            kind="blocked",
            resolution="blocked",
        )
    ]
    payload = policy_blocked_response({"name": "wf"}, issues)
    assert payload["status"] == "blocked"
    assert payload["stage"] == "policy"
    assert payload["can_execute"] is False
    assert payload["policy_issues"][0]["code"] == "policy.approval_required"
