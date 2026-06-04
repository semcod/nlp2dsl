"""
Kontrola dostępu agentów — resource_area + uri_pattern + effect (allow/deny/approval).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.governance.config import get_access_config
from app.governance.uri_match import scheme_allowed, uri_matches


@dataclass
class AccessDecision:
    allowed: bool
    effect: str  # allow | deny | approval
    reason: str = ""
    agent_id: str = ""
    resource_area: str | None = None
    uri: str | None = None
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "effect": self.effect,
            "reason": self.reason,
            "agent_id": self.agent_id,
            "resource_area": self.resource_area,
            "uri": self.uri,
            "action": self.action,
        }


@dataclass(frozen=True)
class _ActionContext:
    area: str | None
    permission_action: str
    target_uri: str | None


def get_agent_id(header_agent: str | None = None) -> str:
    if header_agent and header_agent.strip():
        return header_agent.strip()
    env_agent = os.getenv("NLP2DSL_AGENT_ID", "").strip()
    if env_agent:
        return env_agent
    return get_access_config().default_agent


def _grant_matches(
    grant: dict[str, Any],
    *,
    resource_area: str | None,
    uri: str | None,
    permission_action: str,
) -> bool:
    if not _grant_action_matches(grant, permission_action):
        return False
    return _grant_target_matches(grant, resource_area=resource_area, uri=uri)


def _grant_action_matches(grant: dict[str, Any], permission_action: str) -> bool:
    actions = [str(a).lower() for a in (grant.get("actions") or ["*"])]
    return "*" in actions or permission_action.lower() in actions


def _grant_target_matches(
    grant: dict[str, Any],
    *,
    resource_area: str | None,
    uri: str | None,
) -> bool:
    area_key = grant.get("resource_area") or grant.get("area")
    uri_pattern = grant.get("uri_pattern") or grant.get("uri")

    area_match = _area_selector_match(area_key, resource_area)
    if area_match is not None:
        return area_match

    uri_match = _uri_selector_match(uri_pattern, uri)
    if uri_match is not None:
        return uri_match

    return False


def _area_selector_match(
    area_key: Any,
    resource_area: str | None,
) -> bool | None:
    if area_key and resource_area:
        return area_key == resource_area
    return None


def _uri_selector_match(
    uri_pattern: Any,
    uri: str | None,
) -> bool | None:
    if uri_pattern and uri:
        return uri_matches(str(uri_pattern), uri)
    return None


def authorize_action(
    agent_id: str,
    action_name: str,
    *,
    resource_area: str | None = None,
    uri: str | None = None,
    permission_action: str | None = None,
    action_meta: dict[str, Any] | None = None,
) -> AccessDecision:
    cfg = get_access_config()
    context = _action_context(
        action_meta or {},
        resource_area=resource_area,
        uri=uri,
        permission_action=permission_action,
    )

    scheme_decision = _scheme_decision(
        context,
        allowed_uri_schemes=cfg.allowed_uri_schemes,
        agent_id=agent_id,
        action_name=action_name,
    )
    if scheme_decision:
        return scheme_decision

    agent_cfg = cfg.agents.get(agent_id)
    if not agent_cfg:
        return _unknown_agent_decision(
            agent_id,
            action_name,
            area=context.area,
            target_uri=context.target_uri,
            deny_by_default=cfg.deny_by_default,
        )

    matched_effect = _matched_effect(
        agent_cfg.get("grants") or [],
        resource_area=context.area,
        uri=context.target_uri,
        permission_action=context.permission_action,
    )
    return _effect_decision(matched_effect, agent_id, action_name, context)


def _action_context(
    meta: dict[str, Any],
    *,
    resource_area: str | None,
    uri: str | None,
    permission_action: str | None,
) -> _ActionContext:
    return _ActionContext(
        area=resource_area or meta.get("resource_area"),
        permission_action=(
            permission_action
            or meta.get("permission_action")
            or "execute"
        ).lower(),
        target_uri=uri or meta.get("resource_uri"),
    )


def _scheme_decision(
    context: _ActionContext,
    *,
    allowed_uri_schemes: list[str],
    agent_id: str,
    action_name: str,
) -> AccessDecision | None:
    if context.target_uri and not scheme_allowed(
        context.target_uri,
        allowed_uri_schemes,
    ):
        return _decision(
            False,
            "deny",
            f"scheme_not_allowed:{context.target_uri}",
            agent_id,
            action_name,
            uri=context.target_uri,
        )
    return None


def _effect_decision(
    matched_effect: str | None,
    agent_id: str,
    action_name: str,
    context: _ActionContext,
) -> AccessDecision:
    if matched_effect is None:
        return _decision(
            False,
            "deny",
            "no_matching_grant",
            agent_id,
            action_name,
            context.area,
            context.target_uri,
        )

    if matched_effect == "deny":
        return _decision(
            False,
            "deny",
            "explicit_deny",
            agent_id,
            action_name,
            context.area,
            context.target_uri,
        )

    if matched_effect == "approval":
        return _decision(
            False,
            "approval",
            "requires_approval",
            agent_id,
            action_name,
            context.area,
            context.target_uri,
        )

    return _decision(
        True,
        "allow",
        "granted",
        agent_id,
        action_name,
        context.area,
        context.target_uri,
    )


def _unknown_agent_decision(
    agent_id: str,
    action_name: str,
    *,
    area: str | None,
    target_uri: str | None,
    deny_by_default: bool,
) -> AccessDecision:
    if agent_id in ("anonymous", "user", "default") and not deny_by_default:
        return _decision(
            True,
            "allow",
            "anonymous_allowed",
            agent_id,
            action_name,
            area,
            target_uri,
        )
    if deny_by_default:
        return _decision(False, "deny", "unknown_agent", agent_id, action_name)
    return _decision(True, "allow", "no_agent_policy", agent_id, action_name)


def _matched_effect(
    grants: list[dict[str, Any]],
    *,
    resource_area: str | None,
    uri: str | None,
    permission_action: str,
) -> str | None:
    matched_effect: str | None = None
    for grant in grants:
        if _grant_matches(
            grant,
            resource_area=resource_area,
            uri=uri,
            permission_action=permission_action,
        ):
            matched_effect = str(grant.get("effect", "allow")).lower()
    return matched_effect


def _decision(
    allowed: bool,
    effect: str,
    reason: str,
    agent_id: str,
    action_name: str,
    resource_area: str | None = None,
    uri: str | None = None,
) -> AccessDecision:
    return AccessDecision(
        allowed=allowed,
        effect=effect,
        reason=reason,
        agent_id=agent_id,
        resource_area=resource_area,
        uri=uri,
        action=action_name,
    )
