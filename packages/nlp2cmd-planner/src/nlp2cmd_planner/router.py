"""Select planning strategy for an intent."""

from __future__ import annotations

from pact_ir import IntentIR

from nlp2cmd_planner.strategy import PlanStrategy


class UnsupportedIntentError(ValueError):
    """No planning strategy supports the given intent."""

    def __init__(self, intent: IntentIR):
        super().__init__(
            f"No plan strategy for intent={intent.intent!r} "
            f"target_kind={intent.target_kind.value!r} "
            f"(query={intent.query!r})"
        )
        self.intent = intent


class PlanRouter:
    def __init__(self, strategies: list[PlanStrategy] | None = None):
        from nlp2cmd_planner.strategies.rest_workflow import RestWorkflowPlanStrategy
        from nlp2cmd_planner.strategies.rule_shell import RuleShellPlanStrategy

        self.strategies: list[PlanStrategy] = strategies or [
            RuleShellPlanStrategy(),
            RestWorkflowPlanStrategy(),
        ]

    def select(self, intent: IntentIR) -> PlanStrategy:
        for strategy in self.strategies:
            if strategy.supports(intent):
                return strategy
        raise UnsupportedIntentError(intent)
