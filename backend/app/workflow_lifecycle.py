"""Backend lifecycle helpers for workflow planning and validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.dsl_validation import validate_dsl_for_execution
from app.schemas import RunWorkflowRequest, Step
from nlp2dsl_sdk.workflow import ValidationReport, validation_report_from_issues


def validation_report_for_workflow(workflow: Any) -> ValidationReport:
    """Validate a workflow-like payload and return the canonical report."""
    return validation_report_from_issues(validate_dsl_for_execution(workflow))


def workflow_validation_payload(workflow: Any) -> dict[str, Any]:
    """Response body for `/workflow/validate`."""
    report = validation_report_for_workflow(workflow)
    payload = report.model_dump()
    payload["workflow"] = workflow
    payload["can_execute"] = report.can_execute
    return payload


def workflow_from_lifecycle_body(body: Mapping[str, Any]) -> dict[str, Any] | None:
    """Extract workflow DSL from endpoint bodies that use workflow or dsl keys."""
    if "workflow" in body:
        workflow = body.get("workflow")
    elif "dsl" in body:
        workflow = body.get("dsl")
    else:
        workflow = None
    return workflow if isinstance(workflow, dict) else None


def run_request_from_workflow(workflow: Mapping[str, Any]) -> RunWorkflowRequest:
    """Convert a validated workflow payload into the backend execution request."""
    return RunWorkflowRequest(
        name=str(workflow.get("name") or "nlp_generated"),
        trigger=workflow.get("trigger") or "manual",
        steps=[
            Step(action=str(step["action"]), config=dict(step.get("config") or {}))
            for step in workflow.get("steps", [])
            if isinstance(step, Mapping)
        ],
    )


def attach_validation_to_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Attach DSL validation to a lifecycle plan without changing incomplete plans."""
    workflow = plan.get("workflow")
    if plan.get("status") != "complete" or not workflow:
        return plan

    report = validation_report_for_workflow(workflow)
    plan["validation"] = report.model_dump()
    if not report.can_execute:
        plan["status"] = "validation_failed"
        plan["missing_fields"] = report.missing_fields
    return plan
