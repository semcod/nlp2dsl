"""Tests for LLM-generated contract drafts."""

from __future__ import annotations

from pathlib import Path

import pytest

from nlp2dsl_sdk.contracts.draft import (
    ContractDraft,
    active_draft_contracts,
    draft_ready_for_activation,
    load_draft,
    save_draft,
    validate_draft,
)


def test_validate_draft_accepts_minimal_contract(tmp_path: Path) -> None:
    draft = ContractDraft(
        name="ping_http",
        contract={
            "description": "Ping URL",
            "required": ["url"],
            "category": "business",
            "side_effect": False,
        },
    )
    assert validate_draft(draft) == []


def test_validate_draft_rejects_secrets() -> None:
    draft = ContractDraft(
        name="bad_secret",
        contract={
            "description": "x",
            "required": [],
            "notes": "api_key=super-secret-value",
        },
    )
    issues = validate_draft(draft)
    assert any(i.code == "contract.draft.secret_detected" for i in issues)


def test_draft_ready_for_activation_requires_approved_status() -> None:
    draft = ContractDraft(
        name="ok_action",
        status="draft",
        contract={"description": "x", "required": []},
    )
    assert draft_ready_for_activation(draft) is False

    approved = draft.model_copy(update={"status": "approved"})
    assert draft_ready_for_activation(approved) is True


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    draft = ContractDraft(
        name="roundtrip",
        contract={"description": "demo", "required": ["x"]},
    )
    path = save_draft(draft, root=tmp_path)
    loaded = load_draft(path)
    assert loaded.name == "roundtrip"
    assert loaded.contract["required"] == ["x"]


def test_active_draft_contracts_skips_non_approved(tmp_path: Path) -> None:
    save_draft(
        ContractDraft(
            name="draft_only",
            status="draft",
            contract={"description": "x", "required": []},
        ),
        root=tmp_path,
    )
    save_draft(
        ContractDraft(
            name="live_one",
            status="approved",
            contract={"description": "y", "required": ["channel"]},
        ),
        root=tmp_path,
    )
    active = active_draft_contracts(root=tmp_path)
    assert "draft_only" not in active
    assert "live_one" in active
