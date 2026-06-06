"""Pactown deploy helpers — validate export and produce compose-up instructions."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def validate_pactown_bundle(pactown_dir: Path | str) -> dict[str, Any]:
    """Validate exported pactown directory (ecosystem YAML + service READMEs)."""
    root = Path(pactown_dir)
    eco = root / "nlp2dsl-platform.pactown.yaml"
    issues: list[str] = []
    if not eco.is_file():
        issues.append(f"missing ecosystem: {eco}")
    else:
        try:
            import yaml

            data = yaml.safe_load(eco.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not data.get("services"):
                issues.append("ecosystem YAML missing services block")
        except Exception as exc:
            issues.append(f"invalid ecosystem YAML: {exc}")

    services_dir = root / "services"
    if not services_dir.is_dir():
        issues.append(f"missing services/: {services_dir}")

    pactown_bin = shutil.which("pactown")
    cli_ok = False
    cli_detail = "pactown CLI not installed"
    if pactown_bin and eco.is_file():
        try:
            proc = subprocess.run(
                [pactown_bin, "validate", str(eco)],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            cli_ok = proc.returncode == 0
            cli_detail = (proc.stdout or proc.stderr or "").strip() or f"exit {proc.returncode}"
        except Exception as exc:
            cli_detail = str(exc)

    return {
        "valid": not issues,
        "issues": issues,
        "ecosystem_yaml": str(eco) if eco.is_file() else None,
        "pactown_cli": cli_ok,
        "pactown_cli_detail": cli_detail,
    }


def deploy_instructions(
    *,
    repo_root: Path | str | None = None,
    pactown_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Return commands to deploy nlp2dsl platform (compose) after pactown export."""
    root = Path(repo_root or ".").resolve()
    export_root = Path(pactown_dir) if pactown_dir else root / "examples" / "14-markpact-export" / ".nlp2dsl" / "generated" / "pactown"
    compose_file = root / "docker-compose.yml"

    steps = [
        f"cd {root}",
        "docker compose up -d --build backend nlp-service worker postgres redis",
    ]
    if (root / "trigger-service" / "app" / "main.py").is_file():
        steps.append("docker compose up -d trigger-service")

    validation = validate_pactown_bundle(export_root) if export_root.is_dir() else {
        "valid": False,
        "issues": [f"export dir missing: {export_root}"],
        "pactown_cli": False,
    }

    return {
        "compose_file": str(compose_file),
        "pactown_export": str(export_root),
        "validation": validation,
        "steps": steps,
        "health_checks": [
            "curl -s http://localhost:8010/health",
            "curl -s http://localhost:8012/health",
            "curl -s http://localhost:8004/health",
        ],
    }


def deploy_instructions_json(**kwargs: Any) -> str:
    return json.dumps(deploy_instructions(**kwargs), ensure_ascii=False, indent=2)
