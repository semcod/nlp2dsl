"""Tests for pact-ir models."""

from pact_ir import ExecutionPlanIR, IntentIR, PlanStep, TargetKind


def test_intent_ir_roundtrip_json():
    intent = IntentIR(
        query="find py files",
        intent="file_search",
        domain="shell",
        target_kind=TargetKind.SHELL,
        confidence=0.9,
    )
    restored = IntentIR.model_validate_json(intent.model_dump_json())
    assert restored.intent == "file_search"
    assert restored.target_kind == TargetKind.SHELL


def test_execution_plan_from_intent():
    intent = IntentIR(query="ls src", intent="list", target_kind=TargetKind.SHELL)
    plan = ExecutionPlanIR.from_intent(
        intent,
        source="rule_pipeline",
        steps=[
            PlanStep(
                id="s1",
                action="shell_find",
                target_kind=TargetKind.SHELL,
                params={"path": "src", "name": "*.py"},
                dsl='find src -name "*.py"',
            )
        ],
    )
    assert plan.step_count == 1
    assert plan.primary_target_kind == TargetKind.SHELL
    assert plan.steps[0].dsl.startswith("find")
