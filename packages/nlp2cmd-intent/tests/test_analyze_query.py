"""analyze_query must work with lightweight QueryNormalizer (returns str)."""

import sys

import pytest

from nlp2cmd_intent.input import analyze_query


def test_analyze_query_find_files():
    pytest.importorskip("nlp2cmd_planner")
    data = analyze_query("znajdz pliki *.py", include_plan=True)
    assert data["query"] == "znajdz pliki *.py"
    intent = data["intent_ir"]
    assert intent["intent"] == "find"
    plan = data.get("execution_plan_ir")
    assert plan is not None
    assert plan["steps"][0]["action"] == "shell_find"


def test_analyze_query_without_plan_does_not_require_planner(monkeypatch):
    monkeypatch.setitem(sys.modules, "nlp2cmd_planner", None)

    data = analyze_query("list files in /tmp", include_plan=False)

    assert data["intent_ir"]["target_kind"] == "shell"
    assert "execution_plan_ir" not in data
