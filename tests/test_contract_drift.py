"""Tests for action catalog drift detection."""

from __future__ import annotations

from dsl_validate.contract_drift import (
    build_catalog_drift_report,
    validate_catalog_field_drift,
    validate_handler_drift,
)


def test_validate_handler_drift_detects_missing_handler() -> None:
    issues = validate_handler_drift(
        handler_names=["send_invoice"],
        catalog_names=["send_invoice", "send_email"],
    )
    assert any(issue.code == "handler.missing_for_catalog" for issue in issues)
    assert issues[0].action == "send_email"


def test_validate_catalog_field_drift_detects_required_mismatch() -> None:
    primary = {"send_email": {"required": ["to"], "quality_required": ["body"]}}
    secondary = {"send_email": {"required": ["to", "subject", "body"], "quality_required": ["body"]}}
    issues = validate_catalog_field_drift(primary, secondary, actions=["send_email"])
    assert any(issue.code == "catalog.required_drift" for issue in issues)


def test_build_catalog_drift_report_ok() -> None:
    catalog = {
        "send_invoice": {"required": ["amount", "to"], "quality_required": []},
        "send_email": {"required": ["to"], "quality_required": ["body"]},
    }
    report = build_catalog_drift_report(
        nlp_catalog=catalog,
        worker_handlers=["send_invoice", "send_email"],
    )
    assert report.ok is True
