"""Orientacja zapytania — file_list vs shell vs workflow."""

from __future__ import annotations

import pytest

from app.routing.orientation import orient_query
from app.routing.resolve import resolve_intent


class TestOrientQuery:
    def test_lista_plikow_usera_host_default_mullm(self) -> None:
        o = orient_query("lista plikow usera", connector="mullm")
        assert o.category == "file_list_host"
        assert o.suggested_action == "mullm_shell_task"
        assert o.shell_command == "ls -la /host-home"
        assert o.confidence >= 0.85

    def test_lista_plikow_github_path_hint(self) -> None:
        o = orient_query("lista plikow github", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /host-home/github"
        assert o.list_scope == "github"

    def test_lista_plikow_systemu_root_fs(self) -> None:
        o = orient_query("lista plikow systemu", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /"
        assert o.list_scope == "system"
        assert "orientation_path_system_root" in o.reason_codes

    def test_lista_plikow_linux_host_home(self) -> None:
        o = orient_query("lista plikow linux", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /host-home"
        assert o.list_scope == "host"

    def test_lista_plikow_root_slash(self) -> None:
        o = orient_query("lista plikow /", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /"
        assert "orientation_path_root" in o.reason_codes

    def test_lista_plikow_projektu_nlp2cmd(self) -> None:
        o = orient_query("lista plikow projektu nlp2cmd", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /host-home/github/wronai/nlp2cmd"
        assert o.list_scope == "nlp2cmd"
        assert "orientation_path_project_nlp2cmd" in o.reason_codes

    def test_lista_plikow_w_github_multi_segment(self) -> None:
        o = orient_query("lista plikow w github wronai nlp2cmd", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /host-home/github/wronai/nlp2cmd"
        assert "orientation_path_hint_github_wronai_nlp2cmd" in o.reason_codes

    def test_lista_plikow_projektu_only(self) -> None:
        o = orient_query("lista plikow projektu", connector="mullm")
        assert o.category == "file_list_host"
        assert o.shell_command == "ls -la /host-home/github"
        assert "orientation_path_projects" in o.reason_codes

    def test_lista_plikow_usera_registry(self) -> None:
        o = orient_query("lista plikow usera z rejestru access fabric", connector="mullm")
        assert o.category == "file_list_registry"
        assert o.suggested_action == "mullm_list_files"

    def test_pokaz_pliki_local_connector(self) -> None:
        o = orient_query("pokaż pliki", connector="local")
        assert o.category == "system_local"
        assert o.suggested_action == "system_file_list"

    def test_run_prefix_shell(self) -> None:
        o = orient_query("run ls -la ~", connector="mullm")
        assert o.category == "shell"
        assert o.shell_command == "ls -la ~"

    def test_disk_space_shell_nl(self) -> None:
        o = orient_query("sprawdz miejsce na dysku", connector="mullm")
        assert o.category == "shell"

    def test_invoice_workflow_hint(self) -> None:
        o = orient_query("wyślij fakturę na 100 PLN", connector="mullm")
        assert o.category == "workflow"


class TestResolveIntentOrientation:
    @pytest.mark.asyncio
    async def test_lista_plikow_usera_short_circuit_shell(self) -> None:
        decision, nlp = await resolve_intent("lista plikow usera", connector="mullm")
        assert decision.source == "orientation"
        assert decision.action == "mullm_shell_task"
        assert decision.orientation is not None
        assert decision.orientation["category"] == "file_list_host"
        assert nlp is not None
        assert nlp.entities.shell_command == "ls -la /host-home"

    @pytest.mark.asyncio
    async def test_registry_list_short_circuit_mullm_files(self) -> None:
        decision, nlp = await resolve_intent(
            "lista plikow usera z rejestru access fabric",
            connector="mullm",
        )
        assert decision.action == "mullm_list_files"
        assert decision.orientation["category"] == "file_list_registry"
        assert nlp is not None
