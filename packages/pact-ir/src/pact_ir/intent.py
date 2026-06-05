"""IntentIR — what the user wants, before concrete execution."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pact_ir.target_kind import ExecutionRisk, TargetKind


class Ambiguity(BaseModel):
    field: str
    message: str
    candidates: list[str] = Field(default_factory=list)


class EntityBag(BaseModel):
    """Named entities extracted from NL."""

    values: dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)


class IntentIR(BaseModel):
    """Standardized intent representation (nlp2cmd.intent_ir.v1)."""

    format: str = "nlp2cmd.intent_ir.v1"
    version: int = 1
    query: str
    intent: str = "unknown"
    domain: str = "any"
    entities: EntityBag = Field(default_factory=EntityBag)
    target_kind: TargetKind = TargetKind.UNKNOWN
    constraints: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    execution_risk: ExecutionRisk = ExecutionRisk.LOW
    metadata: dict[str, Any] = Field(default_factory=dict)

    def needs_clarification(self) -> bool:
        return bool(self.ambiguities) or self.confidence < 0.5
