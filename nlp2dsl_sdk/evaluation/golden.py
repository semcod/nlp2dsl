"""Golden dataset cases for NLP→DSL regression evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

ErrorClassFocus = Literal[
    "entity_extraction",
    "dsl_mapping",
    "unnecessary_clarification",
    "unsafe_execution_block",
    "attachment_validation",
]

LifecycleStatus = Literal[
    "complete",
    "incomplete",
    "validation_failed",
    "executed",
    "error",
]


@dataclass(frozen=True)
class GoldenCase:
    """Single golden regression case with expected lifecycle outcome."""

    id: str
    text: str
    focus: ErrorClassFocus
    expected_status: LifecycleStatus
    expected_actions: tuple[str, ...] = ()
    expected_missing: tuple[str, ...] = ()
    mode: str = "rules"
    category: str = "general"
    notes: str = ""

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> GoldenCase:
        return cls(
            id=str(raw["id"]),
            text=str(raw["text"]),
            focus=raw["focus"],  # type: ignore[arg-type]
            expected_status=raw.get("expected_status", "complete"),  # type: ignore[arg-type]
            expected_actions=tuple(str(a) for a in raw.get("expected_actions") or ()),
            expected_missing=tuple(str(m) for m in raw.get("expected_missing") or ()),
            mode=str(raw.get("mode") or "rules"),
            category=str(raw.get("category") or "general"),
            notes=str(raw.get("notes") or ""),
        )


def _data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "golden_cases.yaml"


def load_golden_cases(path: Path | str | None = None) -> tuple[GoldenCase, ...]:
    """Load golden cases from YAML (defaults to bundled dataset)."""
    source = Path(path) if path is not None else _data_path()
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ()
    cases = payload.get("cases") or []
    return tuple(GoldenCase.from_mapping(item) for item in cases if isinstance(item, dict))


def default_golden_cases() -> tuple[GoldenCase, ...]:
    """Return the bundled golden dataset."""
    return load_golden_cases()


def extract_actions(result: dict[str, Any]) -> list[str]:
    """Extract step action names from a lifecycle/from-text response."""
    dsl = (
        result.get("dsl")
        or result.get("workflow")
        or result.get("partial_workflow")
        or {}
    )
    if not isinstance(dsl, dict):
        return []
    steps = dsl.get("steps") or []
    return [str(step.get("action") or "") for step in steps if isinstance(step, dict)]


def extract_missing(result: dict[str, Any]) -> list[str]:
    missing = result.get("missing_fields") or result.get("missing") or []
    if isinstance(missing, str):
        return [missing]
    try:
        return [str(item) for item in missing]
    except TypeError:
        return []


def primary_action(case: GoldenCase) -> str:
    if case.expected_actions:
        return case.expected_actions[0]
    return case.category
