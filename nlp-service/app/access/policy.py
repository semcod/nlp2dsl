"""
Kontrola dostępu agentów — resource_area + uri_pattern + effect (allow/deny/approval).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.access.config import get_access_config
from app.access.uri_match import scheme_allowed, uri_matches


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
    actions = [str(a).lower() for a in (grant.get("actions") or ["*"])]
    if "*" not in actions and permission_action.lower() not in actions:
        return False

    area_key = grant.get("resource_area") or grant.get("area")
    uri_pattern = grant.get("uri_pattern") or grant.get("uri")

    if area_key and resource_area:
        return area_key == resource_area
    if uri_pattern and uri:
        return uri_matches(str(uri_pattern), uri)
    if area_key and not resource_area:
        return False
    if uri_pattern and not uri:
        return False
    return bool(area_key or uri_pattern)


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
    meta = action_meta or {}
    area = resource_area or meta.get("resource_area")
    perm = (permission_action or meta.get("permission_action") or "execute").lower()
    target_uri = uri or meta.get("resource_uri")

    if target_uri and not scheme_allowed(target_uri, cfg.allowed_uri_schemes):
        return AccessDecision(
            allowed=False,
            effect="deny",
            reason=f"scheme_not_allowed:{target_uri}",
            agent_id=agent_id,
            action=action_name,
            uri=target_uri,
        )

    agent_cfg = cfg.agents.get(agent_id)
    if not agent_cfg:
        if agent_id in ("anonymous", "user", "default") and not cfg.deny_by_default:
            return AccessDecision(
                allowed=True,
                effect="allow",
                reason="anonymous_allowed",
                agent_id=agent_id,
                resource_area=area,
                uri=target_uri,
                action=action_name,
            )
        if cfg.deny_by_default:
            return AccessDecision(
                allowed=False,
                effect="deny",
                reason="unknown_agent",
                agent_id=agent_id,
                action=action_name,
            )
        return AccessDecision(
            allowed=True,
            effect="allow",
            reason="no_agent_policy",
            agent_id=agent_id,
            action=action_name,
        )

    grants = agent_cfg.get("grants") or []
    matched_effect: str | None = None
    for grant in grants:
        if not _grant_matches(
            grant,
            resource_area=area,
            uri=target_uri,
            permission_action=perm,
        ):
            continue
        matched_effect = str(grant.get("effect", "allow")).lower()

    if matched_effect is None:
        return AccessDecision(
            allowed=False,
            effect="deny",
            reason="no_matching_grant",
            agent_id=agent_id,
            resource_area=area,
            uri=target_uri,
            action=action_name,
        )

    if matched_effect == "deny":
        return AccessDecision(
            allowed=False,
            effect="deny",
            reason="explicit_deny",
            agent_id=agent_id,
            resource_area=area,
            uri=target_uri,
            action=action_name,
        )

    if matched_effect == "approval":
        return AccessDecision(
            allowed=False,
            effect="approval",
            reason="requires_approval",
            agent_id=agent_id,
            resource_area=area,
            uri=target_uri,
            action=action_name,
        )

    return AccessDecision(
        allowed=True,
        effect="allow",
        reason="granted",
        agent_id=agent_id,
        resource_area=area,
        uri=target_uri,
        action=action_name,
    )
