"""Tests for nlp2dsl run output formatting."""

from __future__ import annotations

from nlp2dsl_sdk.preview import execution_payload, print_run_outcome


def test_execution_payload_prefers_execution_then_result() -> None:
    assert execution_payload({"execution": {"status": "completed"}}) == {"status": "completed"}
    assert execution_payload({"result": {"status": "completed"}}) == {"status": "completed"}
    assert execution_payload({"status": "complete"}) is None


def test_print_run_outcome_shows_invoice_id_and_reflection(capsys) -> None:
    result = {
        "status": "executed",
        "reflection": {
            "phase": "dsl_ready",
            "ready": True,
            "target": {"intent": "send_invoice", "steps": []},
            "issues": [],
            "context_queries": [],
        },
        "autonomous_steps": ["attachment_path (nested generate_invoice)"],
        "autofill_applied": ["send_invoice.attachment_path"],
        "dsl": {
            "name": "auto_send_invoice",
            "steps": [
                {
                    "action": "send_invoice",
                    "config": {
                        "amount": 1500.0,
                        "to": "klient@firma.pl",
                        "attachment_path": "fixtures/faktura-2024.pdf",
                    },
                }
            ],
        },
        "result": {
            "workflow_id": "abc123",
            "status": "completed",
            "steps": [
                {
                    "action": "send_invoice",
                    "status": "completed",
                    "result": {"invoice_id": "INV-001", "sent_to": "klient@firma.pl"},
                }
            ],
        },
    }
    print_run_outcome(result, query="Wyślij fakturę")
    out = capsys.readouterr().out
    assert "INV-001" in out
    assert "Refleksja [dsl_ready]" in out
    assert "Autonomiczne kroki" in out
    assert "Autofill DOQL" in out
    assert "Załącznik faktury" in out
    assert "workflow_id: abc123" in out


def test_detect_example_dir_from_cwd(tmp_path, monkeypatch) -> None:
    from nlp2dsl_sdk.cli import _detect_example_dir

    ex = tmp_path / "13-autonomous-invoice-stack"
    ex.mkdir()
    registry = ex / ".nlp2dsl" / "registry"
    registry.mkdir(parents=True)
    (registry / "environment.doql.less").write_text("// test\n", encoding="utf-8")
    monkeypatch.chdir(ex)
    assert _detect_example_dir() == ex.resolve()
