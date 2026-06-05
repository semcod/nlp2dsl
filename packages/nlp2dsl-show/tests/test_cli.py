import json
import subprocess
import sys


def test_build_query_structure_intent_only():
    from nlp2cmd_intent.input import analyze_query

    data = analyze_query("znajdź pliki *.py w src")
    assert data["query"] == "znajdź pliki *.py w src"
    assert data["intent_ir"]["intent"] in {"find", "file_search", "search"}
    assert data["intent_ir"]["target_kind"] == "shell"
    assert "execution_plan_ir" not in data


def test_build_query_structure_with_plan():
    from nlp2cmd_intent.input import analyze_query

    data = analyze_query("znajdź pliki *.py w src", include_plan=True)
    assert "find" in data["execution_plan_ir"]["steps"][0]["dsl"]


def test_cli_show_json():
    proc = subprocess.run(
        [sys.executable, "-m", "nlp2dsl_show.cli", "show", "znajdź pliki *.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["intent_ir"]["target_kind"] == "shell"


def test_cli_show_rejects_ambiguous_query_when_enforced():
    import os

    env = {**os.environ, "NLP2CMD_ENFORCE_CLARIFICATION": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "nlp2dsl_show.cli", "show", "xyz"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 2
    assert "error:" in proc.stderr
