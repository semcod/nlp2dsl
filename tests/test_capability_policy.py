"""Tests for capability / execution policy layer."""

from __future__ import annotations

from dsl_contracts.registry import contract_from_registry_entry
from env2llm.ir import ProcessAccessScopeIR, ProcessPolicyIR
from dsl_validate.capability_policy import (
    ExecutionPolicyContext,
    validate_capability_policy,
)


def _catalog(*entries: tuple[str, dict]) -> dict:
    return {
        name: contract_from_registry_entry(name, meta).to_catalog_entry()
        for name, meta in entries
    }


def test_dry_run_only_blocks_side_effect_steps() -> None:
    catalog = _catalog(
        (
            "send_email",
            {"required": ["to"], "quality_required": ["body"], "side_effect": True},
        )
    )
    workflow = {
        "steps": [{"action": "send_email", "config": {"to": "a@example.com", "body": "hi"}}],
    }
    ctx = ExecutionPolicyContext(dry_run_only=True, executing=True)
    issues = validate_capability_policy(workflow, catalog, ctx)
    assert len(issues) == 1
    assert issues[0].code == "policy.dry_run_only"


def test_approval_required_without_grant_blocks() -> None:
    catalog = _catalog(
        (
            "send_invoice",
            {
                "required": ["to", "amount"],
                "approval_required": True,
                "side_effect": True,
            },
        )
    )
    workflow = {
        "steps": [{"action": "send_invoice", "config": {"to": "a@b.c", "amount": 100}}],
    }
    issues = validate_capability_policy(workflow, catalog, ExecutionPolicyContext(executing=True))
    assert any(i.code == "policy.approval_required" for i in issues)


def test_approval_grant_allows_execution() -> None:
    catalog = _catalog(
        (
            "send_invoice",
            {"required": ["to", "amount"], "approval_required": True, "side_effect": True},
        )
    )
    workflow = {
        "steps": [{"action": "send_invoice", "config": {"to": "a@b.c", "amount": 100}}],
    }
    ctx = ExecutionPolicyContext(executing=True, approval_grants=frozenset({"send_invoice"}))
    assert validate_capability_policy(workflow, catalog, ctx) == []


def test_email_domain_allowlist() -> None:
    catalog = _catalog(
        (
            "send_email",
            {"required": ["to"], "quality_required": ["body"], "side_effect": True},
        )
    )
    workflow = {
        "steps": [{"action": "send_email", "config": {"to": "x@evil.com", "body": "x"}}],
    }
    ctx = ExecutionPolicyContext(
        executing=True,
        allowed_email_domains=frozenset({"company.com"}),
    )
    issues = validate_capability_policy(workflow, catalog, ctx)
    assert any(i.code == "policy.recipient_not_allowed" for i in issues)


def test_process_scope_denied_mullm() -> None:
    catalog = _catalog(
        (
            "mullm_shell_task",
            {
                "category": "mullm",
                "execution": "delegate",
                "required": ["shell_command"],
                "resource_area": "mullm:rag",
            },
        )
    )
    workflow = {"steps": [{"action": "mullm_shell_task", "config": {"shell_command": "ls"}}]}
    process = ProcessPolicyIR(
        access=ProcessAccessScopeIR(deny_resource_areas=["mullm", "mullm:rag"])
    )
    ctx = ExecutionPolicyContext(executing=True, process=process)
    issues = validate_capability_policy(workflow, catalog, ctx)
    assert any(i.code == "policy.scope_denied" for i in issues)


def test_access_decision_denied_blocks() -> None:
    catalog = _catalog(
        (
            "mullm_shell_task",
            {"category": "mullm", "execution": "delegate", "required": ["shell_command"]},
        )
    )
    workflow = {"steps": [{"action": "mullm_shell_task", "config": {"shell_command": "ls"}}]}
    ctx = ExecutionPolicyContext(
        executing=True,
        agent_id="mail_agent",
        access_decisions={
            "mullm_shell_task": {
                "allowed": False,
                "effect": "deny",
                "reason": "no_matching_grant",
            }
        },
    )
    issues = validate_capability_policy(workflow, catalog, ctx)
    assert any(i.code == "policy.access_denied" for i in issues)
