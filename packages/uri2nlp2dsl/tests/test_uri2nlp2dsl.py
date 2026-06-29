from uri2nlp2dsl.decode import decode_uri, uri_to_dsl
from uri2nlp2dsl.resolve import resolve_nl
from uri2nlp2dsl.uri import build_cmd_uri, parse_uri


def test_build_and_parse_uri() -> None:
    uri = build_cmd_uri("PLAN", text="wyślij fakturę", mode="auto")
    parsed = parse_uri(uri)
    assert parsed.verb == "PLAN"
    assert parsed.params["text"] == "wyślij fakturę"


def test_uri_to_dsl() -> None:
    uri = build_cmd_uri("PARSE", text="hello", mode="llm")
    assert "PARSE" in uri_to_dsl(uri)
    assert "hello" in uri_to_dsl(uri)


def test_decode_uri() -> None:
    uri = build_cmd_uri("HEALTH")
    assert decode_uri(uri) == "HEALTH"


def test_resolve_nl() -> None:
    hits = resolve_nl("zaplanuj workflow faktury")
    assert hits
    assert hits[0].verb == "PLAN"
