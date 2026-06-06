"""Canonical request lifecycle models.

These models are deliberately independent from FastAPI app schemas. Service
layers can adapt their local Pydantic models into this shape while existing
endpoints continue returning their legacy payloads.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, Field

LifecycleStage = Literal["parse", "clarify", "plan", "validate", "simulate", "execute"]
LifecycleStatus = Literal[
    "ready",
    "complete",
    "incomplete",
    "validation_failed",
    "blocked",
    "executed",
    "failed",
    "skipped",
]


class ParseResult(BaseModel):
    """Normalized output of text parsing before deterministic DSL mapping."""

    stage: Literal["parse"] = "parse"
    status: LifecycleStatus = "complete"
    text: str = ""
    mode: str = "auto"
    intent: str = "unknown"
    confidence: float = 0.0
    entities: dict[str, Any] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)
    routing: dict[str, Any] | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ClarificationRequest(BaseModel):
    """Question/form needed before a plan can be considered ready."""

    stage: Literal["clarify"] = "clarify"
    status: LifecycleStatus = "skipped"
    missing_fields: list[str] = Field(default_factory=list)
    prompt_user: str | None = None
    form: dict[str, Any] | None = None
    source_stage: LifecycleStage = "plan"


class ValidationReport(BaseModel):
    """Structured validation result for DSL, runtime and post-execution checks."""

    stage: Literal["validate"] = "validate"
    status: LifecycleStatus = "complete"
    phase: str = "dsl_ready"
    issues: list[dict[str, Any]] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    message: str | None = None

    @property
    def can_execute(self) -> bool:
        return self.status == "complete" and not self.issues


class PlanResult(BaseModel):
    """Normalized workflow plan built from parsed intent and entities."""

    stage: Literal["plan"] = "plan"
    status: LifecycleStatus = "incomplete"
    workflow: dict[str, Any] | None = None
    missing_fields: list[str] = Field(default_factory=list)
    prompt_user: str | None = None
    source: str = "mapper"
    parse: ParseResult | None = None
    clarification: ClarificationRequest | None = None
    validation: ValidationReport | None = None
    trace: list[dict[str, Any]] = Field(default_factory=list)


class ExecutionRequest(BaseModel):
    """Execution envelope for an already planned and validated workflow."""

    stage: Literal["execute"] = "execute"
    status: LifecycleStatus = "ready"
    workflow: dict[str, Any]
    execute: bool = False
    dry_run: bool = False
    idempotency_key: str | None = None
    source: str = "workflow_plan"
    validation: ValidationReport | None = None


def parse_result_from_nlp(
    text: str,
    mode: str,
    nlp_result: Any,
    *,
    routing: Mapping[str, Any] | None = None,
) -> ParseResult:
    """Adapt app-local NLPResult-like objects into a lifecycle ParseResult."""
    raw = _to_dict(nlp_result)
    intent_obj = _get(nlp_result, "intent", {})
    intent = str(_get(intent_obj, "intent", "unknown") or "unknown")
    confidence = _float_or_default(_get(intent_obj, "confidence", 0.0), 0.0)
    entities_obj = _get(nlp_result, "entities", {})
    entities = _compact_dict(_to_dict(entities_obj))
    missing = _string_list(_get(nlp_result, "missing", []))

    return ParseResult(
        status="blocked" if intent == "unknown" else "complete",
        text=text,
        mode=mode,
        intent=intent,
        confidence=confidence,
        entities=entities,
        missing=missing,
        routing=dict(routing) if routing is not None else None,
        raw=raw,
    )


def clarification_from_dialog(
    dialog: Any,
    *,
    source_stage: LifecycleStage = "plan",
) -> ClarificationRequest:
    """Adapt a DialogResponse-like payload into a clarification request."""
    missing_fields = _string_list(_get(dialog, "missing_fields", []))
    prompt_user = _get(dialog, "prompt_user", None)
    return ClarificationRequest(
        status="incomplete" if missing_fields or prompt_user else "skipped",
        missing_fields=missing_fields,
        prompt_user=str(prompt_user) if prompt_user else None,
        source_stage=source_stage,
    )


def plan_result_from_dialog(
    dialog: Any,
    *,
    parse: ParseResult | None = None,
    source: str = "mapper",
    validation: ValidationReport | None = None,
    trace: list[dict[str, Any]] | None = None,
) -> PlanResult:
    """Adapt existing DialogResponse-like objects into a lifecycle PlanResult."""
    status = str(_get(dialog, "status", "incomplete") or "incomplete")
    if status not in {"complete", "incomplete", "validation_failed", "blocked", "failed"}:
        status = "failed" if status == "error" else "incomplete"

    workflow = _get(dialog, "workflow", None)
    workflow_dict = _to_dict(workflow) if workflow is not None else None
    clarification = clarification_from_dialog(dialog)
    missing_fields = _string_list(_get(dialog, "missing_fields", []))
    prompt_user = _get(dialog, "prompt_user", None)

    return PlanResult(
        status=status,  # type: ignore[arg-type]
        workflow=workflow_dict,
        missing_fields=missing_fields,
        prompt_user=str(prompt_user) if prompt_user else None,
        source=source,
        parse=parse,
        clarification=clarification if clarification.status != "skipped" else None,
        validation=validation,
        trace=list(trace or []),
    )


def validation_report_from_issues(
    issues: list[Any],
    *,
    phase: str = "dsl_ready",
    message: str | None = None,
) -> ValidationReport:
    """Build a report from ValidationIssue objects, dicts or legacy strings."""
    payloads = [_issue_to_payload(issue) for issue in issues]
    missing = _missing_fields_from_payloads(payloads)
    return ValidationReport(
        status="validation_failed" if payloads else "complete",
        phase=phase,
        issues=payloads,
        missing_fields=missing,
        message=message,
    )


def execution_request_from_workflow(
    workflow: Any,
    *,
    execute: bool = False,
    dry_run: bool = False,
    idempotency_key: str | None = None,
    source: str = "workflow_plan",
    validation: ValidationReport | None = None,
) -> ExecutionRequest:
    """Wrap a workflow-like object in an execution lifecycle envelope."""
    return ExecutionRequest(
        status="ready" if validation is None or validation.can_execute else "blocked",
        workflow=_to_dict(workflow),
        execute=execute,
        dry_run=dry_run,
        idempotency_key=idempotency_key,
        source=source,
        validation=validation,
    )


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return dict(model_dump())
    legacy_dict = getattr(value, "dict", None)
    if callable(legacy_dict):
        return dict(legacy_dict())
    return {}


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {str(k): v for k, v in value.items() if v is not None}


def _string_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    try:
        return [str(v) for v in raw]
    except TypeError:
        return []


def _float_or_default(raw: Any, default: float) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _issue_to_payload(issue: Any) -> dict[str, Any]:
    to_dict = getattr(issue, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        return dict(payload) if isinstance(payload, Mapping) else {"message": str(payload)}
    if isinstance(issue, Mapping):
        return dict(issue)
    return {
        "code": "legacy.validation_issue",
        "field": "",
        "message": str(issue),
        "phase": "dsl_ready",
        "kind": "invalid_format",
        "resolution": "ask_user",
        "source_hint": None,
        "meta": {},
    }


def _missing_fields_from_payloads(payloads: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for payload in payloads:
        kind = str(payload.get("kind") or "")
        field = str(payload.get("field") or payload.get("field_name") or "")
        if kind != "missing" or not field or field in seen:
            continue
        seen.add(field)
        missing.append(field)
    return missing
