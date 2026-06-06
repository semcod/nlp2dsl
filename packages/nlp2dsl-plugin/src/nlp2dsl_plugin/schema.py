"""Plugin manifest schema (draft → validate → activate)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    description: str = ""
    contracts_dir: str = "contracts"
    executors_dir: str = "executors"
    tests_dir: str = "tests"
    actions: list[str] = Field(default_factory=list)
    requires_backend: list[str] = Field(default_factory=lambda: ["worker"])


def load_plugin_manifest(path: Path | str) -> PluginManifest:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid plugin manifest: {path}")
    return PluginManifest.model_validate(data)


def plugin_layout_valid(plugin_root: Path | str) -> dict[str, Any]:
    root = Path(plugin_root)
    manifest_path = root / "plugin.yaml"
    issues: list[str] = []
    if not manifest_path.is_file():
        issues.append("missing plugin.yaml")
    else:
        try:
            manifest = load_plugin_manifest(manifest_path)
        except Exception as exc:
            issues.append(f"invalid plugin.yaml: {exc}")
            manifest = None
        if manifest is not None:
            for sub in (manifest.contracts_dir, manifest.executors_dir):
                if not (root / sub).is_dir():
                    issues.append(f"missing directory: {sub}/")
    return {"valid": not issues, "issues": issues, "root": str(root)}
