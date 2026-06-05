"""Resolve example root and portable attachment paths (shared Docker volume)."""

from __future__ import annotations

import os
from pathlib import Path

from app.request_context import get_example_dir


def example_root_from_doql(doql_path: Path | str | None) -> Path | None:
    """Map DOQL registry path → example root (host or /examples/NN in Docker)."""
    if not doql_path:
        return None
    path = Path(doql_path)
    parts = path.parts
    if "examples" not in parts:
        return None
    idx = parts.index("examples")
    if idx + 1 >= len(parts):
        return None
    ex_name = parts[idx + 1]
    mount = os.environ.get("NLP2DSL_EXAMPLES_MOUNT", "").strip()
    if mount:
        mounted = Path(mount) / ex_name
        if mounted.is_dir():
            return mounted
    # Host path: .../examples/01-invoice/.nlp2dsl/registry/...
    root = path
    for _ in range(3):
        if root.name == ex_name:
            return root if root.is_dir() else None
        root = root.parent
    return None


def resolve_example_root(*, doql_path: Path | str | None = None) -> Path | None:
    req = get_example_dir()
    if req and ((req / ".nlp2dsl").is_dir() or (req / "fixtures").is_dir()):
        return req
    return example_root_from_doql(doql_path)


def invoice_output_dir(*, doql_path: Path | str | None = None) -> tuple[Path, Path | None]:
    """
    Return (output_directory, example_root).

    Writes under example_root/.nlp2dsl/generated/invoices when possible.
    """
    ex = resolve_example_root(doql_path=doql_path)
    if ex:
        out = ex / ".nlp2dsl" / "generated" / "invoices"
        out.mkdir(parents=True, exist_ok=True)
        return out, ex
    out = Path(os.environ.get("NLP2DSL_INVOICE_DIR", "/tmp/nlp2dsl-invoices"))
    out.mkdir(parents=True, exist_ok=True)
    return out, None


def store_attachment_path(out_path: Path, example_root: Path | None) -> str:
    """Return path storable in DSL — relative to example when possible."""
    if example_root and out_path.is_relative_to(example_root):
        rel = out_path.relative_to(example_root).as_posix()
        mount = os.environ.get("NLP2DSL_EXAMPLES_MOUNT", "").strip()
        if mount:
            portable = (Path(mount) / example_root.name / rel).as_posix()
            if Path(portable).is_file():
                return portable
        return rel
    return str(out_path.resolve())
