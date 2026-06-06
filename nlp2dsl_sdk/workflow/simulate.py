"""Dry-run workflow simulation without side effects."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nlp2dsl_sdk.contracts.registry import SIDE_EFFECT_ACTIONS


def _preview_result(action: str, config: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic stub result for simulate previews."""
    if action == "send_invoice":
        return {
            "invoice_id": "SIM-INV-0001",
            "sent_to": config.get("to"),
            "simulated": True,
        }
    if action == "send_email":
        return {
            "sent_to": config.get("to"),
            "subject": config.get("subject"),
            "simulated": True,
        }
    if action == "generate_report":
        report_type = config.get("report_type", "sales")
        fmt = config.get("format", "pdf")
        return {
            "filename": f"report_{report_type}_SIM.{fmt}",
            "type": report_type,
            "simulated": True,
        }
    if action.startswith("notify_"):
        channel = config.get("channel") or config.get("chat_id") or config.get("webhook_url")
        return {
            "provider": action.replace("notify_", ""),
            "target": channel,
            "message": config.get("message"),
            "simulated": True,
            "transport": "simulated",
        }
    if action == "crm_update":
        return {"entity": config.get("entity", "lead"), "updated": True, "simulated": True}
    if action.startswith("mullm_"):
        return {"backend": "mullm", "action": action, "simulated": True, "delegate": True}
    return {"action": action, "simulated": True}


def simulate_workflow_payload(workflow: Mapping[str, Any]) -> dict[str, Any]:
    """
    Build a simulate-stage response for a workflow DSL.

    Does not call worker or external integrations — preview only.
    """
    steps_in = workflow.get("steps") or []
    simulated_steps: list[dict[str, Any]] = []
    side_effect_count = 0

    for index, raw_step in enumerate(steps_in):
        if not isinstance(raw_step, Mapping):
            continue
        action = str(raw_step.get("action") or "")
        config = dict(raw_step.get("config") or {})
        side_effect = action in SIDE_EFFECT_ACTIONS
        if side_effect:
            side_effect_count += 1
        simulated_steps.append(
            {
                "index": index,
                "action": action,
                "config": config,
                "side_effect": side_effect,
                "simulated": True,
                "preview_result": _preview_result(action, config),
            }
        )

    return {
        "stage": "simulate",
        "status": "ready" if simulated_steps else "validation_failed",
        "workflow": dict(workflow),
        "steps": simulated_steps,
        "step_count": len(simulated_steps),
        "side_effect_count": side_effect_count,
        "can_execute": bool(simulated_steps),
        "dry_run": True,
    }
