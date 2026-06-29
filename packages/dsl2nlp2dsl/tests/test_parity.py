"""Parity: same DSL line → same result shape across adapters (offline verbs)."""

from dsl2nlp2dsl import dispatch
from nlp2nlp2dsl.to_dsl import to_dsl
from uri2nlp2dsl.decode import uri_to_dsl
from uri2nlp2dsl.uri import build_cmd_uri


def test_parity_to_dsl_uri_text() -> None:
    prompt = "validate workflow.json"
    dsl_from_nl = to_dsl(prompt)
    uri = build_cmd_uri("VALIDATE", text=prompt)
    dsl_from_uri = uri_to_dsl(uri)
    assert "VALIDATE" in dsl_from_nl
    assert "VALIDATE" in dsl_from_uri


def test_parity_dispatch_dict_text() -> None:
    line = "HEALTH"
    r1 = dispatch(line)
    r2 = dispatch({"verb": "HEALTH"})
    assert r1.action == r2.action == "health"
