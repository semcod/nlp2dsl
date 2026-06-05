"""ExecutionPlanIR — how to execute an intent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pact_ir.intent import IntentIR
from pact_ir.target_kind import ExecutionRisk, TargetKind


class PlanStep(BaseModel):
    id: str
    action: str
    target_kind: TargetKind
    params: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    risk: ExecutionRisk = ExecutionRisk.LOW
    dsl: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlanIR(BaseModel):
    """Standardized execution plan (nlp2cmd.execution_plan_ir.v1)."""

    format: str = "nlp2cmd.execution_plan_ir.v1"
    version: int = 1
    query: str = ""
    source: str = ""
    confidence: float = 0.0
    steps: list[PlanStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_intent(
        cls,
        intent: IntentIR,
        *,
        steps: list[PlanStep],
        source: str = "",
    ) -> ExecutionPlanIR:
        return cls(
            query=intent.query,
            source=source,
            confidence=intent.confidence,
            steps=steps,
            metadata={"intent": intent.intent, "domain": intent.domain},
        )

    @property
    def primary_target_kind(self) -> TargetKind:
        if not self.steps:
            return TargetKind.UNKNOWN
        return self.steps[0].target_kind

    @property
    def step_count(self) -> int:
        return len(self.steps)
