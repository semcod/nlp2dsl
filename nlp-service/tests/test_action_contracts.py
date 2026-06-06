from __future__ import annotations

from app.registry import get_action_contract, get_action_contracts
from dsl_contracts import action_catalog_payload


def test_registry_exposes_action_contracts() -> None:
    contracts = get_action_contracts()
    assert "send_email" in contracts
    assert contracts["send_email"].required == ["to"]
    assert contracts["send_email"].quality_required == ["body"]


def test_action_contract_payload_preserves_nlp_actions_shape() -> None:
    contract = get_action_contract("send_email")
    assert contract is not None

    payload = action_catalog_payload({"send_email": contract})
    meta = payload["send_email"]

    assert meta["description"] == "Wysyła e-mail"
    assert meta["required"] == ["to"]
    assert meta["optional"] == ["subject", "body"]
    assert meta["quality_required"] == ["body"]
    assert meta["contract_version"] == 1
    assert meta["execution_backend"] == "worker"
