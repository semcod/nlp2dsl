"""Plan strategy protocol."""

from __future__ import annotations

from typing import Protocol

from pact_ir import ExecutionPlanIR, IntentIR


class PlanStrategy(Protocol):
    name: str

    def supports(self, intent: IntentIR) -> bool: ...

    def plan(self, intent: IntentIR) -> ExecutionPlanIR: ...
