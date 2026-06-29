from dsl2nlp2dsl.codec import encode_protobuf, decode_protobuf, roundtrip_protobuf
from dsl2nlp2dsl.pb_codec import dict_to_envelope, envelope_to_dict, encode_result_protobuf, decode_result_protobuf
from dsl2nlp2dsl.result import DslResult
from dsl2nlp2dsl.events import EventStore
from dsl2nlp2dsl.schema_registry import validate_schema_registry


def test_protobuf_roundtrip_text() -> None:
    line = 'PARSE "test query" MODE auto'
    assert roundtrip_protobuf(line) == 'PARSE "test query" MODE auto'


def test_protobuf_envelope_dict_roundtrip() -> None:
    cmd = {"verb": "PLAN", "text": "wyślij fakturę", "mode": "auto"}
    blob = dict_to_envelope(cmd).SerializeToString()
    from dsl2nlp2dsl.v1 import command_pb2

    envelope = command_pb2.DslEnvelope()
    envelope.ParseFromString(blob)
    assert envelope_to_dict(envelope) == cmd


def test_result_protobuf_roundtrip() -> None:
    result = DslResult(ok=True, command='HEALTH', action="health", output="{}", data={})
    blob = encode_result_protobuf(result)
    decoded = decode_result_protobuf(blob)
    assert decoded.ok is True
    assert decoded.action == "health"


def test_eventstore_protobuf_append_replay(tmp_path) -> None:
    store = EventStore(tmp_path / "test.events.pb", fmt="protobuf")
    event = store.append({"verb": "OBSERVE", "target": "."}, {"ok": True, "action": "observe", "output": "{}", "data": {}})
    replayed = store.replay()
    assert len(replayed) == 1
    assert replayed[0].id == event.id
    assert replayed[0].command["verb"] == "OBSERVE"


def test_all_schemas_valid() -> None:
    assert validate_schema_registry() == []
