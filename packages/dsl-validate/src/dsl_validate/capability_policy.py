"""Capability and execution policy checks before side effects run."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from dsl_contracts.issue import Phase, ValidationIssue
from dsl_contracts.registry import action_contracts_from_catalog
from env2llm.ir import ProcessPolicyIR
from env2llm.policy.process import process_scope_denied

_EMAIL_RE = re.compile(r"^[^@\s]+@([^@\s]+)$")
_EMAIL_ACTIONS = frozenset({"send_email", "send_invoice", "generate_invoice"})
_NOTIFY_ACTIONS = frozenset({"notify_slack", "notify_teams", "notify_telegram"})


@dataclass
class ExecutionPolicyContext:
    """Runtime policy envelope applied at pre-execute."""

    agent_id: str = "user"
    executing: bool = True
    dry_run_only: bool = False
    approval_grants: frozenset[str] = field(default_factory=frozenset)
    approval_token: str | None = None
    allowed_email_domains: frozenset[str] = field(default_factory=frozenset)
    allowed_notify_channels: frozenset[str] = field(default_factory=frozenset)
    process: ProcessPolicyIR | None = None
    access_decisions: dict[str, Mapping[str, Any]] = field(default_factory=dict)


def _workflow_steps(workflow: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [s for s in (workflow.get("steps") or []) if isinstance(s, Mapping)]


def _step_config(step: Mapping[str, Any]) -> dict[str, Any]:
    raw = step.get("config") or step.get("parameters") or {}
    return dict(raw) if isinstance(raw, Mapping) else {}


def _email_domain(address: str) -> str | None:
    match = _EMAIL_RE.match(str(address or "").strip())
    return match.group(1).lower() if match else None


def _target_uri(action: str, config: Mapping[str, Any]) -> str | None:
    if action in _EMAIL_ACTIONS:
        recipient = str(config.get("to") or "").strip()
        return f"mailto:{recipient}" if recipient else None
    webhook = str(config.get("webhook_url") or "").strip()
    if webhook:
        return webhook
    return None


def _approval_granted(
    action: str,
    config: Mapping[str, Any],
    ctx: ExecutionPolicyContext,
) -> bool:
    if action in ctx.approval_grants:
        return True
    step_token = str(config.get("approval_token") or "").strip()
    if ctx.approval_token and step_token and step_token == ctx.approval_token:
        return True
    if ctx.approval_token and not step_token and action in ctx.approval_grants:
        return True
    return False


def _blocked_issue(
    *,
    code: str,
    field_name: str,
    message: str,
    phase: Phase,
    meta: dict[str, Any],
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        field_name=field_name,
        message=message,
        phase=phase,
        kind="blocked",
        resolution="blocked",
        meta=meta,
    )


def _scope_issue(
    *,
    step_ref: str,
    action: str,
    area: str | None,
    denied: str,
    phase: Phase,
) -> ValidationIssue:
    return _blocked_issue(
        code="policy.scope_denied",
        field_name=step_ref,
        message=denied,
        phase=phase,
        meta={"action": action, "resource_area": area},
    )


def _dry_run_issue(*, step_ref: str, action: str, phase: Phase) -> ValidationIssue:
    return _blocked_issue(
        code="policy.dry_run_only",
        field_name=step_ref,
        message=f"Akcja `{action}` ma efekt uboczny — tryb dry_run_only blokuje wykonanie.",
        phase=phase,
        meta={"action": action},
    )


def _approval_issue(*, step_ref: str, action: str, phase: Phase) -> ValidationIssue:
    return _blocked_issue(
        code="policy.approval_required",
        field_name=step_ref,
        message=(
            f"Akcja `{action}` wymaga zatwierdzenia (approval_required). "
            "Przekaż approval_grants lub approval_token."
        ),
        phase=phase,
        meta={"action": action},
    )


def _access_denied_issue(
    *,
    step_ref: str,
    action: str,
    ctx: ExecutionPolicyContext,
    effect: str,
    reason: str,
    phase: Phase,
) -> ValidationIssue:
    return _blocked_issue(
        code="policy.access_denied",
        field_name=step_ref,
        message=(
            f"Agent `{ctx.agent_id}` nie może wykonać `{action}` "
            f"(effect={effect}, reason={reason})."
        ),
        phase=phase,
        meta={
            "action": action,
            "agent_id": ctx.agent_id,
            "effect": effect,
            "reason": reason,
        },
    )


def _recipient_issue(
    *,
    step_ref: str,
    action: str,
    domain: str,
    allowed: frozenset[str],
    phase: Phase,
) -> ValidationIssue:
    return _blocked_issue(
        code="policy.recipient_not_allowed",
        field_name=f"{step_ref}.config.to",
        message=(
            f"Domena `{domain}` nie jest na liście dozwolonych odbiorców "
            f"({', '.join(sorted(allowed))})."
        ),
        phase=phase,
        meta={"action": action, "domain": domain},
    )


def _channel_issue(
    *,
    step_ref: str,
    action: str,
    channel: str,
    allowed: frozenset[str],
    phase: Phase,
) -> ValidationIssue:
    return _blocked_issue(
        code="policy.channel_not_allowed",
        field_name=f"{step_ref}.config.channel",
        message=(
            f"Kanał `{channel}` nie jest dozwolony "
            f"({', '.join(sorted(allowed))})."
        ),
        phase=phase,
        meta={"action": action, "channel": channel},
    )


def _check_process_scope(
    *,
    action: str,
    contract: Any,
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    if ctx.process is None:
        return None
    area = contract.resource_area if contract else None
    denied = process_scope_denied(ctx.process, action=action, resource_area=area)
    if not denied:
        return None
    return _scope_issue(step_ref=step_ref, action=action, area=area, denied=denied, phase=phase)


def _check_dry_run(
    *,
    action: str,
    contract: Any,
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    if not (ctx.dry_run_only and ctx.executing and contract and contract.execution.side_effect):
        return None
    return _dry_run_issue(step_ref=step_ref, action=action, phase=phase)


def _check_approval(
    *,
    action: str,
    config: Mapping[str, Any],
    contract: Any,
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    if not (ctx.executing and contract and contract.execution.approval_required):
        return None
    if _approval_granted(action, config, ctx):
        return None
    return _approval_issue(step_ref=step_ref, action=action, phase=phase)


def _check_access_decision(
    *,
    action: str,
    config: Mapping[str, Any],
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    decision = ctx.access_decisions.get(action)
    if not (ctx.executing and decision and not decision.get("allowed")):
        return None
    effect = str(decision.get("effect") or "deny")
    if effect == "approval" and _approval_granted(action, config, ctx):
        return None
    reason = str(decision.get("reason") or effect)
    return _access_denied_issue(
        step_ref=step_ref,
        action=action,
        ctx=ctx,
        effect=effect,
        reason=reason,
        phase=phase,
    )


def _check_email_domain(
    *,
    action: str,
    config: Mapping[str, Any],
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    if not (ctx.executing and ctx.allowed_email_domains and action in _EMAIL_ACTIONS):
        return None
    recipient = str(config.get("to") or "").strip()
    domain = _email_domain(recipient)
    if not domain or domain in ctx.allowed_email_domains:
        return None
    return _recipient_issue(
        step_ref=step_ref,
        action=action,
        domain=domain,
        allowed=ctx.allowed_email_domains,
        phase=phase,
    )


def _check_notify_channel(
    *,
    action: str,
    config: Mapping[str, Any],
    ctx: ExecutionPolicyContext,
    step_ref: str,
    phase: Phase,
) -> ValidationIssue | None:
    if not (ctx.executing and ctx.allowed_notify_channels and action in _NOTIFY_ACTIONS):
        return None
    channel = str(config.get("channel") or config.get("chat_id") or "").strip()
    if not channel or channel in ctx.allowed_notify_channels:
        return None
    return _channel_issue(
        step_ref=step_ref,
        action=action,
        channel=channel,
        allowed=ctx.allowed_notify_channels,
        phase=phase,
    )


def _validate_step_policy(
    *,
    index: int,
    step: Mapping[str, Any],
    contract: Any,
    ctx: ExecutionPolicyContext,
    phase: Phase,
) -> list[ValidationIssue]:
    action = str(step.get("action") or "")
    if not action:
        return []
    config = _step_config(step)
    step_ref = f"steps.{index}"
    issues: list[ValidationIssue] = []

    scope_issue = _check_process_scope(
        action=action, contract=contract, ctx=ctx, step_ref=step_ref, phase=phase
    )
    if scope_issue:
        return [scope_issue]
    if not contract:
        return []

    for check in (
        lambda: _check_dry_run(action=action, contract=contract, ctx=ctx, step_ref=step_ref, phase=phase),
        lambda: _check_approval(action=action, config=config, contract=contract, ctx=ctx, step_ref=step_ref, phase=phase),
        lambda: _check_access_decision(action=action, config=config, ctx=ctx, step_ref=step_ref, phase=phase),
        lambda: _check_email_domain(action=action, config=config, ctx=ctx, step_ref=step_ref, phase=phase),
        lambda: _check_notify_channel(action=action, config=config, ctx=ctx, step_ref=step_ref, phase=phase),
    ):
        issue = check()
        if issue is None:
            continue
        issues.append(issue)
        if issue.code == "policy.access_denied":
            return issues
    return issues


def validate_capability_policy(
    workflow: Mapping[str, Any],
    catalog: Mapping[str, Any],
    ctx: ExecutionPolicyContext,
    *,
    phase: Phase = Phase.PRE_EXECUTE,
) -> list[ValidationIssue]:
    """Return policy violations that must block execution before the worker."""
    contracts = action_contracts_from_catalog(catalog)
    issues: list[ValidationIssue] = []

    for index, step in enumerate(_workflow_steps(workflow)):
        action = str(step.get("action") or "")
        contract = contracts.get(action) if action else None
        issues.extend(
            _validate_step_policy(
                index=index,
                step=step,
                contract=contract,
                ctx=ctx,
                phase=phase,
            )
        )
    return issues


def access_decision_requires_approval(decision: Mapping[str, Any]) -> bool:
    return str(decision.get("effect") or "") == "approval" and not decision.get("allowed")


def build_access_decision_params(
    action: str,
    config: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any],
) -> dict[str, str]:
    """Query params for nlp-service GET /nlp/access/check."""
    contracts = action_contracts_from_catalog(catalog)
    contract = contracts.get(action)
    params: dict[str, str] = {
        "agent_id": "",
        "action": action,
        "permission_action": "execute",
    }
    if contract:
        params["permission_action"] = str(contract.permission_action or "execute")
        if contract.resource_area:
            params["resource_area"] = str(contract.resource_area)
    uri = _target_uri(action, config)
    if uri:
        params["uri"] = uri
    return params
