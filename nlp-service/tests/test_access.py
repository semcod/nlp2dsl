"""Testy nlp2dsl.yaml — ACL, URI, native routing."""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # repo root (nlp2dsl/)
CONFIG = ROOT / "nlp2dsl.yaml"


@pytest.fixture(autouse=True)
def _point_config(monkeypatch):
    monkeypatch.setenv("NLP2DSL_CONFIG", str(CONFIG))
    from app.access import config as cfg_mod

    cfg_mod._CONFIG = None


def test_config_loads_areas():
    from app.access.config import get_access_config

    cfg = get_access_config()
    assert any(a.get("id") == "mullm:rag" for a in cfg.resource_areas)
    assert "files_agent" in cfg.agents


def test_uri_match_mullm():
    from app.access.uri_match import uri_matches

    assert uri_matches("mullm://**", "mullm://ticket/abc")
    assert uri_matches("mullm://ticket/*", "mullm://ticket/abc")
    assert not uri_matches("mullm://ticket/*", "mullm://localfs/x")


def test_files_agent_can_list():
    from app.access.policy import authorize_action

    d = authorize_action(
        "files_agent",
        "mullm_list_files",
        resource_area="mullm:rag",
        permission_action="list",
    )
    assert d.allowed
    assert d.effect == "allow"


def test_mail_agent_denied_mullm_execute():
    from app.access.policy import authorize_action

    d = authorize_action(
        "mail_agent",
        "mullm_shell_task",
        resource_area="mullm:rag",
        permission_action="execute",
    )
    assert not d.allowed


def test_native_lista_plikow_registry():
    from app.routing.native import resolve_native_intent

    hit = resolve_native_intent("lista plikow usera z rejestru")
    assert hit is not None
    assert hit["action"] == "mullm_list_files"


def test_registry_has_yaml_action():
    from app.registry import ACTIONS_REGISTRY

    meta = ACTIONS_REGISTRY["mullm_list_files"]
    assert meta.get("resource_area") == "mullm:rag"
    assert "lista plikow" in [a.lower() for a in meta["aliases"]]
