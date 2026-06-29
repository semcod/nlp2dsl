"""to_dsl + dispatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dsl2nlp2dsl import DslResult, dispatch
from nlp2nlp2dsl.to_dsl import to_dsl


@dataclass
class ApplyResult:
    ok: bool
    prompt: str
    dsl: str = ""
    action: str = ""
    output: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "prompt": self.prompt,
            "dsl": self.dsl,
            "action": self.action,
            "output": self.output,
            "data": self.data,
            "error": self.error,
        }


def apply_nl(
    prompt: str,
    *,
    mode: str = "auto",
    default_file: str | None = None,
    out: str | None = None,
) -> ApplyResult:
    line = to_dsl(prompt, mode=mode)
    if out and "OUT" not in line:
        line += f" OUT {out}"
    result: DslResult = dispatch(line, default_file=default_file)
    return ApplyResult(
        ok=result.ok,
        prompt=prompt,
        dsl=line,
        action=result.action,
        output=result.output,
        data=result.data,
        error=result.error,
    )
