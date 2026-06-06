"""Tests for markpact / pactown export from ActionContract + DSL."""

from __future__ import annotations

from pathlib import Path

from dsl_contracts import contract_from_registry_entry
from workflow_export.markpact import (
    export_markpact_bundle,
    workflow_dsl_to_markpact_readme,
)
from workflow_export.pactown import export_pactown_bundle, nlp2dsl_platform_ecosystem


def _sample_catalog() -> dict:
    return {
        "generate_report": contract_from_registry_entry(
            "generate_report",
            {
                "description": "Generuje raport",
                "required": ["report_type"],
                "optional": {"format": "pdf"},
            },
        ).to_catalog_entry(),
        "send_email": contract_from_registry_entry(
            "send_email",
            {
                "description": "Wysyła e-mail",
                "required": ["to", "subject", "body"],
                "quality_required": ["body"],
            },
        ).to_catalog_entry(),
    }


def _sample_dsl() -> dict:
    return {
        "name": "report_and_email",
        "trigger": "daily",
        "steps": [
            {
                "action": "generate_report",
                "config": {"report_type": "sales", "format": "pdf"},
            },
            {
                "action": "send_email",
                "config": {
                    "to": "manager@firma.pl",
                    "subject": "Raport sprzedaży",
                    "body": "W załączeniu raport sales.",
                },
            },
        ],
    }


def test_workflow_dsl_to_markpact_readme_contains_blocks() -> None:
    from dsl_contracts import action_contracts_from_catalog

    catalog = _sample_catalog()
    contracts = action_contracts_from_catalog(catalog)
    md = workflow_dsl_to_markpact_readme(
        _sample_dsl(),
        contracts,
        source_query="Codziennie raport PDF i email do manager@firma.pl",
    )
    assert "markpact:file path=workflows/report_and_email.workflow.yaml" in md
    assert "markpact:file path=contracts/generate_report.contract.yaml" in md
    assert "markpact:file path=contracts/send_email.contract.yaml" in md
    assert "markpact:test http" in md
    assert "report_and_email" in md


def test_export_markpact_bundle_writes_files(tmp_path: Path) -> None:
    bundle = export_markpact_bundle(
        tmp_path / "markpact",
        _sample_dsl(),
        _sample_catalog(),
        source_query="test query",
    )
    assert bundle.readme.is_file()
    assert bundle.workflow_yaml.is_file()
    assert bundle.workflow_json.is_file()
    assert len(bundle.contract_files) == 2
    text = bundle.readme.read_text(encoding="utf-8")
    assert "generate_report" in text
    assert (tmp_path / "markpact" / "contracts" / "send_email.contract.yaml").is_file()


def test_export_pactown_bundle(tmp_path: Path) -> None:
    markpact = export_markpact_bundle(
        tmp_path / "markpact",
        _sample_dsl(),
        _sample_catalog(),
    )
    pactown = export_pactown_bundle(
        tmp_path / "pactown",
        markpact_readme=markpact.readme,
    )
    assert pactown.ecosystem_yaml.is_file()
    eco = pactown.ecosystem_yaml.read_text(encoding="utf-8")
    assert "report-and-email" in eco
    assert (tmp_path / "pactown" / "services" / "backend" / "README.md").is_file()
    assert (tmp_path / "pactown" / "services" / "report-and-email" / "README.md").is_file()


def test_publish_layer_bundle(tmp_path) -> None:
    from dsl_contracts import action_catalog_payload, contract_from_registry_entry
    from workflow_export.publish import export_workflow_publish_layer

    catalog = action_catalog_payload(
        {
            "generate_report": contract_from_registry_entry(
                "generate_report", {"required": ["report_type"], "optional": {"format": "pdf"}}
            ),
            "send_email": contract_from_registry_entry(
                "send_email", {"required": ["to", "subject", "body"]}
            ),
        }
    )
    dsl = {
        "name": "report_and_email",
        "trigger": "daily",
        "steps": [
            {"action": "generate_report", "config": {"report_type": "sales"}},
            {"action": "send_email", "config": {"to": "a@b.pl", "subject": "x", "body": "y"}},
        ],
    }
    bundle = export_workflow_publish_layer(
        tmp_path,
        dsl,
        catalog,
        source_query="test",
    )
    assert bundle.markpact.readme.is_file()
    assert bundle.pactown.ecosystem_yaml.is_file()
