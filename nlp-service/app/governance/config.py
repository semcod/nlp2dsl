"""
Ładowanie nlp2dsl.yaml — zasoby, agenci, uprawnienia, routing natywny.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger("access.config")

_CONFIG: "AccessConfig | None" = None


def _search_paths() -> list[Path]:
    env_path = os.getenv("NLP2DSL_CONFIG", "").strip()
    paths: list[Path] = []
    if env_path:
        paths.append(Path(env_path))
    cwd = Path.cwd()
    for name in ("nlp2dsl.yaml", "nlp2dsl.local.yaml", ".nlp2dsl.yaml"):
        paths.append(cwd / name)
    repo_root = Path(__file__).resolve().parents[3]
    paths.append(repo_root / "nlp2dsl.yaml")
    paths.append(repo_root / "nlp2dsl.local.yaml")
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


@dataclass
class AccessConfig:
    version: int = 1
    path: str | None = None
    default_agent: str = "anonymous"
    deny_by_default: bool = True
    enabled_integrations: list[str] = field(default_factory=lambda: ["mullm"])
    allowed_uri_schemes: list[str] = field(
        default_factory=lambda: ["mullm", "file", "http", "https", "docker"]
    )
    resource_areas: list[dict[str, Any]] = field(default_factory=list)
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    native_routes: list[dict[str, Any]] = field(default_factory=list)
    label_groups: list[dict[str, Any]] = field(default_factory=list)

    def action_to_area(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for area in self.resource_areas:
            aid = area.get("id") or area.get("area_id") or ""
            for action_name in (area.get("actions") or {}):
                out[action_name] = aid
        return out

    def area_by_id(self, area_id: str) -> dict[str, Any] | None:
        for area in self.resource_areas:
            if (area.get("id") or area.get("area_id")) == area_id:
                return area
        return None


def _load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def _merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = {**base}
    for key, val in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _merge_dict(out[key], val)
        elif key in out and isinstance(out[key], list) and isinstance(val, list):
            out[key] = out[key] + val
        else:
            out[key] = val
    return out


def load_access_config(*, force: bool = False) -> AccessConfig:
    global _CONFIG
    if _CONFIG is not None and not force:
        return _CONFIG

    merged, loaded_path = _load_merged_config()
    _CONFIG = _build_access_config(merged, loaded_path)
    return _CONFIG


def _load_merged_config() -> tuple[dict[str, Any], str | None]:
    merged: dict[str, Any] = {}
    loaded_path: str | None = None
    for path in _search_paths():
        if not path.is_file():
            continue
        try:
            merged = _merge_dict(merged, _load_yaml_file(path))
            loaded_path = str(path)
            log.info("Loaded access config from %s", path)
        except Exception as exc:
            log.warning("Skip config %s: %s", path, exc)
    return merged, loaded_path


def _build_access_config(merged: dict[str, Any], loaded_path: str | None) -> AccessConfig:
    ac = merged.get("access_control") or {}
    settings = merged.get("settings") or {}
    return AccessConfig(
        version=int(merged.get("version", 1)),
        path=loaded_path,
        default_agent=_default_agent(settings, ac),
        deny_by_default=bool(ac.get("deny_by_default", True)),
        enabled_integrations=_enabled_integrations(merged),
        allowed_uri_schemes=_allowed_uri_schemes(ac),
        resource_areas=list(merged.get("resource_areas") or []),
        agents=dict(merged.get("agents") or {}),
        native_routes=list(merged.get("native_routing") or []),
        label_groups=list(merged.get("label_groups") or []),
    )


def _enabled_integrations(merged: dict[str, Any]) -> list[str]:
    integrations = merged.get("integrations") or {}
    if isinstance(integrations, dict):
        enabled = integrations.get("enabled") or integrations.get("names") or ["mullm"]
    else:
        enabled = integrations or ["mullm"]
    return [str(item) for item in enabled]


def _default_agent(settings: dict[str, Any], access_control: dict[str, Any]) -> str:
    return str(
        settings.get("default_agent")
        or access_control.get("default_agent")
        or "anonymous"
    )


def _allowed_uri_schemes(access_control: dict[str, Any]) -> list[str]:
    schemes = access_control.get("allowed_uri_schemes") or [
        "mullm",
        "file",
        "http",
        "https",
    ]
    return [str(scheme) for scheme in schemes]


def get_access_config() -> AccessConfig:
    return load_access_config()


def reload_access_config() -> AccessConfig:
    return load_access_config(force=True)
