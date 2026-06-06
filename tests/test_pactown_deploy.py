"""Tests for pactown deploy helpers."""

from __future__ import annotations

from pathlib import Path

from nlp2dsl_sdk.deploy.pactown_deploy import deploy_instructions, validate_pactown_bundle


def test_validate_pactown_bundle_missing_dir(tmp_path: Path) -> None:
    result = validate_pactown_bundle(tmp_path / "missing")
    assert result["valid"] is False
    assert result["issues"]


def test_validate_pactown_bundle_minimal(tmp_path: Path) -> None:
    eco = tmp_path / "nlp2dsl-platform.pactown.yaml"
    eco.write_text(
        "name: test\nservices:\n  backend:\n    port: 8010\n",
        encoding="utf-8",
    )
    (tmp_path / "services").mkdir()
    result = validate_pactown_bundle(tmp_path)
    assert result["valid"] is True
    assert result["ecosystem_yaml"] == str(eco)


def test_deploy_instructions_includes_compose_steps() -> None:
    repo = Path(__file__).resolve().parents[1]
    payload = deploy_instructions(repo_root=repo, pactown_dir=repo / "nonexistent")
    assert "docker compose up" in payload["steps"][1]
    assert payload["compose_file"].endswith("docker-compose.yml")
