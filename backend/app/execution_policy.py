"""Backend adapter — capability/policy gate before workflow execution."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from httpx import AsyncClient

from app.action_catalog import load_action_field_catalog
from app.dsl_validation import (
    dsl_validation_response,
    missing_fields_from_issues,
    validation_issue_payloads,
)
from app.engine import NLP_SERVICE_URL
from app.logging_setup import get_request_id
from dsl_validate.capability_policy import (
    ExecutionPolicyContext,
    build_access_decision_params,
    validate_capability_policy,
)
from dsl_validate.issue import ValidationIssue
from env2llm.ir import ProcessAccessScopeIR, ProcessPolicyIR


def resolve_agent_id(body: Mapping[str, Any], *, header_agent: str | None = None) -> str:
    explicit = str(body.get("agent_id") or "").strip()
    if explicit:
        return explicit
    if header_agent and header_agent.strip():
        return header_agent.strip()
    env_agent = os.getenv("NLP2DSL_AGENT_ID", "").strip()
    if env_agent:
        return env_agent
    return "user"


def _as_str_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [p.strip() for p in raw.split(",") if p.strip()]
    try:
        return [str(x).strip() for x in raw if str(x).strip()]
    except TypeError:
        return []


def _policy_blocks(body: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    policy_block = body.get("policy") if isinstance(body.get("policy"), Mapping) else {}
    process_block = body.get("process") if isinstance(body.get("process"), Mapping) else {}
    return policy_block, process_block


def _approval_grants(body: Mapping[str, Any], policy_block: Mapping[str, Any]) -> frozenset[str]:
    raw = body.get("approval_grants") or policy_block.get("approval_grants") or []
    if isinstance(raw, str):
        raw = [raw]
    return frozenset(str(x).strip() for x in raw if str(x).strip())


def _process_policy_from_block(process_block: Mapping[str, Any]) -> ProcessPolicyIR | None:
    access_raw = process_block.get("access") if isinstance(process_block.get("access"), Mapping) else None
    if not access_raw:
        return None
    return ProcessPolicyIR(
        access=ProcessAccessScopeIR(
            agent=str(access_raw.get("agent") or ""),
            allow_resource_areas=_as_str_list(
                access_raw.get("allow_resource_areas") or access_raw.get("allow_areas")
            ),
            deny_resource_areas=_as_str_list(
                access_raw.get("deny_resource_areas") or access_raw.get("deny_areas")
            ),
        )
    )


def _dry_run_only(body: Mapping[str, Any], policy_block: Mapping[str, Any]) -> bool:
    return bool(
        body.get("dry_run_only")
        or policy_block.get("dry_run_only")
        or os.getenv("NLP2DSL_DRY_RUN_ONLY", "").lower() in {"1", "true", "yes"}
    )


def build_policy_context(
    body: Mapping[str, Any],
    *,
    agent_id: str | None = None,
    executing: bool = True,
    access_decisions: dict[str, Mapping[str, Any]] | None = None,
) -> ExecutionPolicyContext:
    policy_block, process_block = _policy_blocks(body)
    email_domains = policy_block.get("allowed_email_domains") or []
    notify_channels = policy_block.get("allowed_notify_channels") or []

    return ExecutionPolicyContext(
        agent_id=agent_id or resolve_agent_id(body),
        executing=executing,
        dry_run_only=_dry_run_only(body, policy_block),
        approval_grants=_approval_grants(body, policy_block),
        approval_token=str(body.get("approval_token") or policy_block.get("approval_token") or "").strip()
        or None,
        allowed_email_domains=frozenset(str(x).lower().strip() for x in email_domains if str(x).strip()),
        allowed_notify_channels=frozenset(str(x).strip() for x in notify_channels if str(x).strip()),
        process=_process_policy_from_block(process_block),
        access_decisions=dict(access_decisions or {}),
    )


async def fetch_access_decisions(
    workflow: Mapping[str, Any],
    *,
    agent_id: str,
    catalog: Mapping[str, Any] | None = None,
    nlp_service_url: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve agent ACL per workflow step via nlp-service /nlp/access/check."""
    catalog = catalog or load_action_field_catalog()
    base = (nlp_service_url or NLP_SERVICE_URL).rstrip("/")
    decisions: dict[str, dict[str, Any]] = {}
    steps = [s for s in (workflow.get("steps") or []) if isinstance(s, Mapping)]

    async with AsyncClient(timeout=10.0, headers={"X-Request-ID": get_request_id()}) as client:
        for step in steps:
            action = str(step.get("action") or "")
            if not action or action in decisions:
                continue
            config = dict(step.get("config") or {}) if isinstance(step.get("config"), Mapping) else {}
            params = build_access_decision_params(action, config, catalog=catalog)
            params["agent_id"] = agent_id
            try:
                resp = await client.get(f"{base}/nlp/access/check", params=params)
                if resp.is_success:
                    payload = resp.json()
                    if isinstance(payload, dict):
                        decisions[action] = payload
            except Exception:
                continue
    return decisions


async def validate_workflow_execution_policy(
    workflow: Mapping[str, Any],
    body: Mapping[str, Any],
    *,
    executing: bool = True,
    header_agent: str | None = None,
    skip_access_check: bool = False,
) -> list[ValidationIssue]:
    catalog = load_action_field_catalog()
    agent_id = resolve_agent_id(body, header_agent=header_agent)
    access_decisions: dict[str, Mapping[str, Any]] = {}
    if executing and not skip_access_check:
        access_decisions = await fetch_access_decisions(
            workflow,
            agent_id=agent_id,
            catalog=catalog,
        )

    ctx = build_policy_context(
        body,
        agent_id=agent_id,
        executing=executing,
        access_decisions=access_decisions,
    )
    return validate_capability_policy(workflow, catalog, ctx)


def policy_blocked_response(dsl: Any, issues: list[ValidationIssue]) -> dict[str, Any]:
    missing = missing_fields_from_issues(issues)
    payload = dsl_validation_response(dsl, issues)
    payload["status"] = "blocked"
    payload["stage"] = "policy"
    payload["message"] = "Polityka wykonania blokuje workflow:\n" + "\n".join(
        f"  • {issue.to_legacy_message()}" for issue in issues
    )
    payload["policy_issues"] = validation_issue_payloads(issues)
    payload["missing_fields"] = missing
    payload["can_execute"] = False
    return payload
