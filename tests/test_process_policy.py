"""Tests for process policy → SystemMapIR → DOQL."""

from __future__ import annotations

from nlp2dsl_sdk.example_bootstrap import ensure_doql_registry
from nlp2dsl_sdk.process_policy import (
    apply_process_policies,
    effective_nlp_parser_mode,
    load_platform_process_defaults,
    merge_process_config,
    process_policy_from_profile_block,
    process_scope_denied,
)
from nlp2dsl_sdk.system_map_bridge import doql_file_to_system_map
from nlp2dsl_sdk.system_map_generator import generate_system_map
from nlp2dsl_sdk.system_map_ir import ProcessPolicyIR, SystemMapIR
from nlp2dsl_sdk.system_map_render import render_system_map_doql


def test_process_policy_from_profile_deterministic() -> None:
    proc = process_policy_from_profile_block(
        {
            "mode": "deterministic",
            "nlp": {"parser": "rules_first", "enrich_missing": False},
            "access": {"agent": "user", "deny_resource_areas": ["mullm:rag"]},
            "paths": {"artifacts_read": ["fixtures/**"], "artifacts_write": ["out/**"]},
        }
    )
    assert proc.mode == "deterministic"
    assert proc.nlp_parser == "rules_first"
    assert proc.nlp_confidence_min == 0.85
    assert proc.access.agent == "user"
    assert proc.access.deny_resource_areas == ["mullm:rag"]
    assert proc.paths.read == ["fixtures/**"]
    assert effective_nlp_parser_mode(proc) == "rules"


def test_apply_process_policies_merges_conversation() -> None:
    ir = SystemMapIR(example_id="01-invoice")
    apply_process_policies(ir, example_id="01-invoice", repo_root=".")
    assert ir.process.mode == "deterministic"
    assert ir.process.nlp_parser == "rules_first"
    assert ir.conversation.sync_auto_execute is True


def test_render_and_roundtrip_process_block(tmp_path) -> None:
    ir = SystemMapIR(
        example_id="test",
        process=ProcessPolicyIR(
            mode="reactive",
            nlp_parser="llm",
            llm_reasoning="deep",
            access={"agent": "user", "deny_resource_areas": ["docker:local"]},
            paths={"read": ["fixtures/**"], "write": ["generated/**"]},
        ),
    )
    doql = render_system_map_doql(ir)
    assert "process {" in doql
    assert 'mode: "reactive"' in doql
    assert "process_access {" in doql
    assert "paths {" in doql

    path = tmp_path / "environment.doql.less"
    path.write_text(doql, encoding="utf-8")
    loaded = doql_file_to_system_map(path)
    assert loaded.process.mode == "reactive"
    assert loaded.process.nlp_parser == "llm"
    assert loaded.process.access.deny_resource_areas == ["docker:local"]
    assert loaded.process.paths.read == ["fixtures/**"]


def test_generate_system_map_01_invoice_has_process() -> None:
    ir = generate_system_map("examples/01-invoice", example_id="01-invoice")
    assert ir.process.mode == "deterministic"
    assert ir.process.nlp_parser == "rules_first"
    doql = render_system_map_doql(ir)
    assert 'nlp_parser: "rules_first"' in doql


def test_ensure_doql_registry_writes_process_block() -> None:
    path = ensure_doql_registry("examples/01-invoice", example_id="01-invoice", auto_execute=False)
    text = path.read_text(encoding="utf-8")
    assert "process {" in text
    assert "deterministic" in text


def test_platform_defaults_merge_with_example() -> None:
    platform = load_platform_process_defaults(".")
    assert platform.get("mode") == "balanced"
    merged = merge_process_config(
        repo_root=".",
        example_block={"mode": "deterministic", "nlp": {"parser": "rules_first"}},
    )
    assert merged["mode"] == "deterministic"
    assert merged["nlp"]["parser"] == "rules_first"
    assert merged["nlp"]["confidence_min"] == 0.5  # from platform defaults


def test_process_scope_denied_mullm() -> None:
    proc = process_policy_from_profile_block(
        {"access": {"deny_resource_areas": ["mullm:rag"]}}
    )
    msg = process_scope_denied(proc, action="mullm_list_files", resource_area="mullm:rag")
    assert msg is not None
    assert "mullm:rag" in msg

