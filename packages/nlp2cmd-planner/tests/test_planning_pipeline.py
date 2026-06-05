from nlp2cmd_planner import PlanningPipeline
from nlp2cmd_planner.router import UnsupportedIntentError
from nlp2cmd_planner.strategies.rule_shell import RuleShellPlanStrategy, _parse_file_search
from pact_ir import EntityBag, IntentIR, TargetKind
import pytest


def test_planning_pipeline_shell_find():
    plan = PlanningPipeline().run("znajdź pliki *.py")
    assert plan.step_count == 1
    assert plan.steps[0].target_kind.value == "shell"
    assert plan.steps[0].dsl == 'find . -name "*.py"'
    assert plan.steps[0].action == "shell_find"


def test_planning_pipeline_shell_find_with_path():
    plan = PlanningPipeline().run("znajdź pliki *.py w src")
    assert plan.steps[0].dsl == 'find src -name "*.py"'
    assert plan.steps[0].params["path"] == "src"
    assert plan.steps[0].params["name"] == "*.py"


def test_rule_shell_supports_find_intent():
    intent = IntentIR(
        query="find files",
        intent="find",
        domain="shell",
        target_kind=TargetKind.SHELL,
    )
    assert RuleShellPlanStrategy().supports(intent)


def test_parse_file_search_from_entities():
    intent = IntentIR(
        query="ignored",
        intent="find",
        entities=EntityBag(values={"path": "src", "pattern": "*.py"}),
    )
    assert _parse_file_search(intent) == ("src", "*.py")


def test_unsupported_intent_raises():
    intent = IntentIR(
        query="wejdź na example.com",
        intent="navigate",
        domain="browser",
        target_kind=TargetKind.BROWSER,
    )
    from nlp2cmd_planner.router import PlanRouter

    with pytest.raises(UnsupportedIntentError):
        PlanRouter().select(intent)
