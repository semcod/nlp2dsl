from nlp2nlp2dsl.to_dsl import to_dsl


def test_to_dsl_plan() -> None:
    line = to_dsl("zaplanuj wyślij fakturę")
    assert line.startswith("PLAN")


def test_to_dsl_validate_file() -> None:
    line = to_dsl("validate workflow.json")
    assert "VALIDATE" in line
    assert "workflow.json" in line


def test_to_dsl_no_side_effect() -> None:
    line = to_dsl("parse test query")
    assert "PARSE" in line
    assert "test query" in line
