from dsl2nlp2dsl.bus import execute_dsl_line
from dsl2nlp2dsl.codec import roundtrip_text
from dsl2nlp2dsl.grammar import parse_line, to_text
from dsl2nlp2dsl.schema_registry import validate_schema_registry


def test_parse_grammar() -> None:
    cmd = parse_line('PLAN "wyślij fakturę" MODE auto')
    assert cmd["verb"] == "PLAN"
    assert cmd["text"] == "wyślij fakturę"
    assert cmd["mode"] == "auto"


def test_roundtrip() -> None:
    line = 'PARSE "test query" MODE llm'
    assert roundtrip_text(line) == to_text(parse_line(line))


def test_validate_schema_registry() -> None:
    assert validate_schema_registry() == []


def test_draft_validate_local() -> None:
    result = execute_dsl_line("DRAFT nonexistent-draft-xyz")
    assert result.ok is False
