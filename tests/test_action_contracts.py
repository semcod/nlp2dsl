from __future__ import annotations

from nlp2dsl_sdk.contracts import (
    action_catalog_payload,
    action_contracts_from_catalog,
    action_info_config_schema,
    contract_from_registry_entry,
)


def test_contract_from_registry_entry_preserves_legacy_action_fields() -> None:
    contract = contract_from_registry_entry(
        "send_email",
        {
            "description": "Wysyła e-mail",
            "required": ["to"],
            "quality_required": ["body"],
            "optional": {"subject": "Automatyczna wiadomość", "body": ""},
            "aliases": ["email"],
            "param_aliases": {"treść": "body"},
        },
    )

    assert contract.name == "send_email"
    assert contract.required == ["to"]
    assert contract.optional_fields == ["subject", "body"]
    assert contract.quality_required == ["body"]
    assert contract.execution.backend == "worker"
    assert contract.execution.idempotency == "required"
    assert action_info_config_schema(contract) == {
        "to": "str",
        "subject": "str",
        "body": "str",
    }


def test_contract_marks_delegate_execution_from_registry() -> None:
    contract = contract_from_registry_entry(
        "mullm_shell_task",
        {
            "description": "Shell",
            "category": "mullm",
            "execution": "delegate",
            "required": ["shell_command"],
            "optional": {"title": "Task"},
        },
    )

    assert contract.category == "mullm"
    assert contract.execution.backend == "delegate"
    assert contract.execution.mode == "delegate"


def test_action_catalog_payload_roundtrip_is_backward_compatible() -> None:
    contract = contract_from_registry_entry(
        "send_invoice",
        {
            "description": "Faktura",
            "required": ["amount", "to"],
            "optional": {"currency": "PLN"},
            "aliases": ["faktura"],
        },
    )

    payload = action_catalog_payload({"send_invoice": contract})
    assert payload["send_invoice"]["required"] == ["amount", "to"]
    assert payload["send_invoice"]["optional"] == ["currency"]
    assert payload["send_invoice"]["contract_version"] == 1

    roundtrip = action_contracts_from_catalog(payload)["send_invoice"]
    assert roundtrip.required == ["amount", "to"]
    assert roundtrip.optional_fields == ["currency"]
