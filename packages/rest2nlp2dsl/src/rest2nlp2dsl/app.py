"""FastAPI app — text/json/protobuf DSL dispatch."""

from __future__ import annotations

import json
from pathlib import Path

from dsl2nlp2dsl import dispatch
from dsl2nlp2dsl.events import default_event_store
from dsl2nlp2dsl.pb_codec import encode_result_protobuf
from dsl2nlp2dsl.schema_registry import all_schemas, schema_for_verb

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse, PlainTextResponse, Response as RawResponse
except ImportError as exc:
    raise RuntimeError("REST support requires: pip install rest2nlp2dsl") from exc

_PROTO_DIR = Path(__file__).resolve().parents[3] / "dsl2nlp2dsl" / "proto" / "dsl2nlp2dsl" / "v1"


def create_app() -> FastAPI:
    app = FastAPI(title="rest2nlp2dsl", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rest2nlp2dsl"}

    @app.get("/v1/schema/{verb}")
    def get_schema(verb: str) -> JSONResponse:
        schema = schema_for_verb(verb)
        if schema is None:
            return JSONResponse({"error": f"unknown verb: {verb}"}, status_code=404)
        return JSONResponse(schema)

    @app.get("/v1/schema")
    def list_schemas() -> JSONResponse:
        return JSONResponse(all_schemas())

    @app.get("/v1/proto")
    def list_proto() -> JSONResponse:
        files = {}
        if _PROTO_DIR.is_dir():
            for path in sorted(_PROTO_DIR.glob("*.proto")):
                files[path.name] = path.read_text(encoding="utf-8")
        return JSONResponse({"package": "dsl2nlp2dsl.v1", "files": files})

    @app.get("/v1/events")
    def list_events(file: str = "app.nlp2dsl.less", format: str = "json") -> Response:
        store = default_event_store(file)
        events = [e.to_dict() for e in store.replay()]
        if format == "pb":
            from dsl2nlp2dsl.v1 import result_pb2
            from dsl2nlp2dsl.pb_codec import dict_to_envelope, result_to_pb
            from dsl2nlp2dsl.result import DslResult

            chunks = bytearray()
            for event in store.replay():
                pb = result_pb2.DslEvent()
                pb.id = event.id
                pb.ts_unix = event.ts_unix
                pb.correlation_id = event.correlation_id
                pb.command.CopyFrom(dict_to_envelope(event.command, correlation_id=event.correlation_id))
                dsl_result = DslResult(
                    ok=bool(event.result.get("ok")),
                    command=str(event.result.get("command", "")),
                    action=str(event.result.get("action", "")),
                    output=str(event.result.get("output", "")),
                    data=dict(event.result.get("data") or {}),
                    error=event.result.get("error"),
                    event_id=event.id,
                )
                pb.result.CopyFrom(result_to_pb(dsl_result))
                data = pb.SerializeToString()
                chunks.extend(len(data).to_bytes(4, "big"))
                chunks.extend(data)
            return RawResponse(bytes(chunks), media_type="application/x-protobuf")
        return JSONResponse(events)

    async def _handle_body(request: Request, default_file: str = "") -> Response:
        content_type = request.headers.get("content-type", "text/plain").split(";")[0].strip()
        body = await request.body()
        if content_type == "application/json":
            envelope = json.loads(body.decode("utf-8"))
            result = dispatch(envelope, default_file=default_file or None)
        elif content_type == "application/x-protobuf":
            result = dispatch(body, default_file=default_file or None)
            return RawResponse(encode_result_protobuf(result), media_type="application/x-protobuf")
        else:
            line = body.decode("utf-8").strip()
            result = dispatch(line, default_file=default_file or None)
        if content_type == "text/plain":
            return PlainTextResponse(result.output or json.dumps(result.to_dict(), ensure_ascii=False))
        return JSONResponse(result.to_dict())

    @app.post("/v1/dsl")
    async def post_dsl(request: Request, file: str = "") -> Response:
        return await _handle_body(request, default_file=file)

    @app.post("/v1/commands")
    async def post_commands(request: Request, file: str = "") -> Response:
        return await _handle_body(request, default_file=file)

    return app
