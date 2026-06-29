"""EventStore — protobuf (*.events.pb) + jsonl dev fallback."""

from __future__ import annotations

import base64
import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from dsl2nlp2dsl.v1 import command_pb2, result_pb2
from dsl2nlp2dsl.pb_codec import dict_to_envelope, envelope_to_dict, pb_to_result, result_to_pb
from dsl2nlp2dsl.result import DslResult

StoreFormat = Literal["protobuf", "jsonl"]


@dataclass
class DslEvent:
    id: str
    ts_unix: int
    command: dict[str, Any]
    result: dict[str, Any]
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventStore:
    def __init__(self, path: Path | str, *, fmt: StoreFormat | None = None) -> None:
        self.path = Path(path)
        if fmt is not None:
            self.fmt: StoreFormat = fmt
        elif self.path.suffix == ".pb":
            self.fmt = "protobuf"
        else:
            self.fmt = "jsonl"

    def append(
        self,
        command: dict[str, Any],
        result: dict[str, Any],
        *,
        correlation_id: str = "",
    ) -> DslEvent:
        event = DslEvent(
            id=str(uuid.uuid4()),
            ts_unix=int(time.time()),
            command=command,
            result=result,
            correlation_id=correlation_id,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.fmt == "protobuf":
            self._append_pb(event)
        else:
            self._append_jsonl(event)
        return event

    def _append_pb(self, event: DslEvent) -> None:
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
        with self.path.open("ab") as fh:
            data = pb.SerializeToString()
            fh.write(len(data).to_bytes(4, "big"))
            fh.write(data)

    def _append_jsonl(self, event: DslEvent) -> None:
        row = event.to_dict()
        if self.path.suffix == ".jsonl":
            try:
                envelope = dict_to_envelope(event.command, correlation_id=event.correlation_id)
                dsl_result = DslResult(
                    ok=bool(event.result.get("ok")),
                    command=str(event.result.get("command", "")),
                    action=str(event.result.get("action", "")),
                    output=str(event.result.get("output", "")),
                    data=dict(event.result.get("data") or {}),
                    error=event.result.get("error"),
                    event_id=event.id,
                )
                pb_event = result_pb2.DslEvent()
                pb_event.id = event.id
                pb_event.ts_unix = event.ts_unix
                pb_event.correlation_id = event.correlation_id
                pb_event.command.CopyFrom(envelope)
                pb_event.result.CopyFrom(result_to_pb(dsl_result))
                row["pb"] = base64.b64encode(pb_event.SerializeToString()).decode("ascii")
            except Exception:
                pass
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def replay(self) -> list[DslEvent]:
        if not self.path.is_file():
            return []
        if self.fmt == "protobuf":
            return self._replay_pb()
        return self._replay_jsonl()

    def _replay_pb(self) -> list[DslEvent]:
        events: list[DslEvent] = []
        data = self.path.read_bytes()
        offset = 0
        while offset + 4 <= len(data):
            size = int.from_bytes(data[offset : offset + 4], "big")
            offset += 4
            chunk = data[offset : offset + size]
            offset += size
            pb = result_pb2.DslEvent()
            pb.ParseFromString(chunk)
            events.append(
                DslEvent(
                    id=pb.id,
                    ts_unix=int(pb.ts_unix),
                    command=envelope_to_dict(pb.command),
                    result=pb_to_result(pb.result).to_dict(),
                    correlation_id=pb.correlation_id,
                )
            )
        return events

    def _replay_jsonl(self) -> list[DslEvent]:
        events: list[DslEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            if "pb" in raw:
                pb = result_pb2.DslEvent()
                pb.ParseFromString(base64.b64decode(raw["pb"]))
                events.append(
                    DslEvent(
                        id=pb.id,
                        ts_unix=int(pb.ts_unix),
                        command=envelope_to_dict(pb.command),
                        result=pb_to_result(pb.result).to_dict(),
                        correlation_id=pb.correlation_id,
                    )
                )
            else:
                events.append(DslEvent(**{k: raw[k] for k in ("id", "ts_unix", "command", "result", "correlation_id") if k in raw}))
        return events


def default_event_store(manifest_file: str = "app.nlp2dsl.less", *, prefer_pb: bool = True) -> EventStore:
    stem = Path(manifest_file).stem.replace("app.", "")
    if prefer_pb:
        return EventStore(Path(f"app.{stem}.events.pb"), fmt="protobuf")
    return EventStore(Path(f"app.{stem}.events.jsonl"), fmt="jsonl")
