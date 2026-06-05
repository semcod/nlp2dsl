"""REST planning via nlp2dsl workflow backend."""

from __future__ import annotations

import json

from pact_ir import ExecutionPlanIR, IntentIR, PlanStep, TargetKind

from nlp2cmd_planner.router import UnsupportedIntentError
from nlp2cmd_planner.workflow_backend import (
    fetch_workflow_from_text,
    workflow_backend_enabled,
    workflow_run_path,
)

_WORKFLOW_INTENTS = frozenset(
    {
        "send_invoice",
        "send_email",
        "generate_report",
        "generate_report_and_notify",
        "create_scheduled_report",
        "notify_slack",
        "crm_update",
        "send_invoice_and_notify",
        "workflow",
        "api_call",
        "rest",
    }
)
_WORKFLOW_DOMAINS = frozenset({"workflow", "api", "rest", "backend"})


class RestWorkflowPlanStrategy:
    name = "rest_workflow"

    def supports(self, intent: IntentIR) -> bool:
        if not workflow_backend_enabled():
            return False
        if intent.target_kind == TargetKind.REST:
            return True
        if intent.intent in _WORKFLOW_INTENTS:
            return True
        return intent.domain in _WORKFLOW_DOMAINS

    def plan(self, intent: IntentIR) -> ExecutionPlanIR:
        payload = fetch_workflow_from_text(intent.query)
        if not payload or payload.get("status") != "complete":
            raise UnsupportedIntentError(intent)

        workflow = payload.get("dsl") or {}
        steps_data = workflow.get("steps") or []
        if not steps_data:
            raise UnsupportedIntentError(intent)

        run_body = {
            "name": workflow.get("name", "nlp_generated"),
            "trigger": workflow.get("trigger", "manual"),
            "steps": steps_data,
        }
        endpoint = workflow_run_path()
        plan_step = PlanStep(
            id="s1",
            action="workflow_run",
            target_kind=TargetKind.REST,
            params={
                "method": "POST",
                "endpoint": endpoint,
                "body": run_body,
                "backend_url": payload.get("backend_url"),
            },
            dsl=f"POST {endpoint}",
            description=f"Run workflow {run_body['name']}",
            metadata={
                "workflow_source": "nlp2dsl_backend",
                "workflow_actions": [step.get("action") for step in steps_data],
            },
        )
        plan = ExecutionPlanIR.from_intent(intent, steps=[plan_step], source=self.name)
        plan.metadata["workflow_dsl"] = workflow
        plan.metadata["backend_base_url"] = payload.get("backend_url")
        return plan
