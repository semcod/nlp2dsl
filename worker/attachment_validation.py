"""Worker attachment validation (lightweight — no dsl_validate in slim Docker image)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from path_resolve import resolve_worker_attachment_path


def build_attachment_validation(
    raw_path: str,
    *,
    action: str = "send_invoice",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = str(raw_path or "").strip()
    if not raw:
        return {"path": "", "resolved": "", "status": "skipped", "issues": []}

    resolved = resolve_worker_attachment_path(raw)
    issues: list[str] = []
    status = "ok"
    resolved_path = Path(resolved)

    if not resolved_path.is_file():
        status = "missing"
        issues.append(f"attachment_path: plik nie istnieje: {raw}")
    elif action == "send_invoice" and resolved_path.suffix.lower() == ".pdf":
        header = resolved_path.read_bytes()[:5]
        if header != b"%PDF-":
            status = "invalid"
            issues.append("attachment_path: oczekiwany binarny PDF (%PDF-)")

    return {"path": raw, "resolved": resolved, "status": status, "issues": issues}


def validate_invoice_attachment(raw_path: str, config: dict[str, Any]) -> dict[str, Any]:
    return build_attachment_validation(raw_path, action="send_invoice", config=config)
