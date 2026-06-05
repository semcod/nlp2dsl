"""End-to-end intent → plan pipeline."""

from __future__ import annotations

from pact_ir import ExecutionPlanIR

from nlp2cmd_intent import IntentPipeline
from nlp2cmd_planner.router import PlanRouter


class PlanningPipeline:
    def __init__(
        self,
        *,
        intent_pipeline: IntentPipeline | None = None,
        router: PlanRouter | None = None,
    ):
        self.intent_pipeline = intent_pipeline or IntentPipeline()
        self.router = router or PlanRouter()

    def run(self, query: str) -> ExecutionPlanIR:
        intent = self.intent_pipeline.run(query)
        strategy = self.router.select(intent)
        return strategy.plan(intent)
