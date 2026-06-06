"""Tests for compose_generator — stack + cron artifact emission."""

from __future__ import annotations

from pathlib import Path

import yaml

from nlp2dsl_stack import generate_stack_compose
from env2llm.ir import DeploySpecIR, ScheduleSpecIR, SystemMapIR


def test_generate_stack_compose_writes_artifacts(tmp_path: Path) -> None:
    ex = tmp_path / "13-autonomous-invoice-stack"
    ex.mkdir()
    (ex / "fixtures").mkdir()

    ir = SystemMapIR(
        example_id="13-autonomous-invoice-stack",
        schedules=[
            ScheduleSpecIR(
                id="daily-invoice",
                cron="0 9 * * *",
                task="Wyślij fakturę",
                workflow_action="send_invoice",
            )
        ],
        deploy=DeploySpecIR(
            docker_profiles=["invoice", "autonomous-stack"],
            stack_compose=".nlp2dsl/generated/docker-compose.stack.yaml",
        ),
    )

    result = generate_stack_compose(ir, example_dir=ex, example_id="13-autonomous-invoice-stack")

    assert result.stack_compose.is_file()
    assert result.crontab.is_file()
    assert result.run_script.is_file()
    assert result.manifest.is_file()
    assert (ex / ".nlp2dsl/generated/services/process-shell/Dockerfile").is_file()
    assert (ex / ".nlp2dsl/generated/services/stack-cron/Dockerfile").is_file()

    payload = yaml.safe_load(result.stack_compose.read_text(encoding="utf-8"))
    assert "invoice-stack-cron" in payload["services"]
    assert "process-shell" in payload["services"]
    assert "build" in payload["services"]["process-shell"]

    crontab = result.crontab.read_text(encoding="utf-8")
    assert "0 9 * * *" in crontab
    assert "daily-invoice" in crontab

    manifest = yaml.safe_load(result.manifest.read_text(encoding="utf-8"))
    assert manifest["example_id"] == "13-autonomous-invoice-stack"
    assert "up_command" in manifest


def test_enrich_ir_adds_defaults(tmp_path: Path) -> None:
    ex = tmp_path / "13-autonomous-invoice-stack"
    ex.mkdir()

    ir = SystemMapIR(example_id="13-autonomous-invoice-stack")
    result = generate_stack_compose(ir, example_dir=ex)

    manifest = yaml.safe_load(result.manifest.read_text(encoding="utf-8"))
    assert len(manifest["schedules"]) >= 1
    assert manifest["deploy"]["target"] == "docker-compose"
