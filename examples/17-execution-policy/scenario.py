"""Przykład 17 — capability/policy layer (approval, ACL, allowlisty)."""

from __future__ import annotations

from typing import Any, Optional

from nlp2dsl_sdk.client import NLP2DSLClient, workflow_step
from nlp2dsl_sdk.preview import ensure_services

ALLOWED_DOMAIN = "company.com"
RECIPIENT_OK = f"finance@{ALLOWED_DOMAIN}"
RECIPIENT_BAD = "finance@evil.example"


def _invoice_workflow(*, recipient: str) -> dict[str, Any]:
    return {
        "name": "policy_demo_invoice",
        "trigger": "manual",
        "steps": [
            workflow_step(
                "send_invoice",
                to=recipient,
                amount=500,
                currency="PLN",
            )
        ],
    }


def _mullm_workflow() -> dict[str, Any]:
    return {
        "name": "policy_demo_mullm",
        "trigger": "manual",
        "steps": [workflow_step("mullm_shell_task", shell_command="echo policy-demo")],
    }


def _policy_layer_active(client: NLP2DSLClient) -> bool:
    """True when backend implements check_policy (requires rebuilt backend image)."""
    probe = client.workflow_validate(
        _invoice_workflow(recipient=RECIPIENT_BAD),
        check_policy=True,
        policy={"allowed_email_domains": [ALLOWED_DOMAIN]},
        skip_access_check=True,
    )
    return probe.get("status") == "blocked" or bool(probe.get("policy_issues"))


def _print_policy_result(label: str, payload: dict[str, Any]) -> None:
    status = payload.get("status")
    print(f"\n▶ {label}")
    print(f"   status={status}")
    if payload.get("policy_issues"):
        for issue in payload["policy_issues"]:
            print(f"   • [{issue.get('code')}] {issue.get('message')}")
    elif payload.get("validation_issues"):
        for issue in payload["validation_issues"]:
            print(f"   • [{issue.get('code')}] {issue.get('message')}")
    elif status == "blocked":
        print("   🚫 blocked")
    elif status in {"complete", "ready", "executed"}:
        print("   ✅ OK")
    if payload.get("can_execute") is False:
        print("   can_execute=False")


def run(client: Optional[NLP2DSLClient] = None) -> dict[str, Any]:
    client = client or NLP2DSLClient.from_env()
    print("=== Przykład 17: Execution policy (capability layer) ===\n")

    if not ensure_services(client):
        return {}

    if not _policy_layer_active(client):
        print(
            "⚠️  Backend nie obsługuje check_policy (stary obraz Docker).\n"
            "   Przebuduj i uruchom ponownie z repo root:\n"
            "     docker compose build backend && docker compose up -d backend\n"
            "   Potem: cd examples/17-execution-policy && python3 main.py\n"
        )
        raise SystemExit(1)

    results: dict[str, Any] = {}

    bad_wf = _invoice_workflow(recipient=RECIPIENT_BAD)
    results["domain_blocked"] = client.workflow_validate(
        bad_wf,
        check_policy=True,
        policy={"allowed_email_domains": [ALLOWED_DOMAIN]},
        skip_access_check=True,
    )
    _print_policy_result("Validate — domena spoza allowlisty", results["domain_blocked"])

    ok_wf = _invoice_workflow(recipient=RECIPIENT_OK)
    results["domain_ok"] = client.workflow_validate(
        ok_wf,
        check_policy=True,
        policy={"allowed_email_domains": [ALLOWED_DOMAIN]},
        skip_access_check=True,
    )
    _print_policy_result("Validate — domena na allowliście", results["domain_ok"])

    results["execute_no_grant"] = client.workflow_execute(
        ok_wf,
        skip_access_check=True,
        policy={"allowed_email_domains": [ALLOWED_DOMAIN]},
    )
    _print_policy_result("Execute — bez approval_grants (może blocked)", results["execute_no_grant"])

    if results["execute_no_grant"].get("status") == "blocked":
        results["execute_with_grant"] = client.workflow_execute(
            ok_wf,
            approval_grants=["send_invoice"],
            skip_access_check=True,
            policy={"allowed_email_domains": [ALLOWED_DOMAIN]},
        )
        _print_policy_result("Execute — z approval_grants", results["execute_with_grant"])
    else:
        print("\n▶ Execute przeszedł bez approval — pomijam krok z grantem (brak approval_required w katalogu)")
        results["execute_with_grant"] = results["execute_no_grant"]

    results["acl_blocked"] = client.workflow_validate(
        _mullm_workflow(),
        check_policy=True,
        agent_id="mail_agent",
    )
    _print_policy_result("Validate — mail_agent vs mullm_shell_task (ACL)", results["acl_blocked"])

    domain_block_ok = results["domain_blocked"].get("status") == "blocked"
    domain_allow_ok = results["domain_ok"].get("status") != "blocked"
    acl_ok = results["acl_blocked"].get("status") == "blocked"
    print("\n--- Podsumowanie ---")
    print(f"   allowlist blokuje evil domenę: {'OK' if domain_block_ok else 'FAIL'}")
    print(f"   allowlist przepuszcza company.com: {'OK' if domain_allow_ok else 'FAIL'}")
    print(f"   ACL mail_agent→mullm: {'OK' if acl_ok else 'FAIL'}")

    if not (domain_block_ok and domain_allow_ok and acl_ok):
        raise SystemExit(1)

    return results
