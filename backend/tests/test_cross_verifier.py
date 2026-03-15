from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from backend.app.models.case import Case
from backend.app.services.cross_verifier import cross_verify


def _document(document_id: str, category: str):
    return SimpleNamespace(id=document_id, user_category=category)


def _extraction(document, key: str, numeric: str | None = None, text: str | None = None):
    return SimpleNamespace(
        document_id=document.id,
        document=document,
        schema_field_key=key,
        value_numeric=None if numeric is None else Decimal(numeric),
        user_edited_value=None,
        value=text if text is not None else numeric,
    )


def test_cross_verify_adds_india_specific_high_risk_flags() -> None:
    current_year = date.today().year
    case = Case(
        id="case-risk-flags",
        company_name="Risk Demo Finance Limited",
        cin=f"U65990MH{current_year - 1}PTC000001",
    )
    gstr_3b_doc = _document("gst-3b", "GST_Returns")
    gstr_2a_doc = _document("gst-2a", "GST_Returns")
    share_doc = _document("share-1", "Shareholding_Pattern")
    portfolio_doc = _document("portfolio-1", "Portfolio_Performance")

    checks = cross_verify(
        case,
        [],
        [
            _extraction(gstr_3b_doc, "return_type", text="GSTR-3B"),
            _extraction(gstr_3b_doc, "turnover_reported", numeric="131"),
            _extraction(gstr_2a_doc, "return_type", text="GSTR-2A"),
            _extraction(gstr_2a_doc, "turnover_reported", numeric="100"),
            _extraction(share_doc, "shares_pledged_percent", numeric="80"),
            _extraction(portfolio_doc, "gnpa_percent", numeric="12"),
        ],
    )

    notes = {check["note"] for check in checks}
    check_names = {check["check_name"] for check in checks}

    assert "GSTR-3B vs 2A Reconciliation (MEDIUM)" not in check_names
    assert "GSTR-3B vs 2A Reconciliation (HIGH)" in check_names
    assert any("GSTR-3B vs 2A discrepancy of 31.0% detected" in note for note in notes)
    assert "CIN Company Age (MEDIUM)" in check_names
    assert any("Company incorporated 1 year(s) ago" in note for note in notes)
    assert "Promoter Pledge Threshold (HIGH)" in check_names
    assert any("CRITICAL: Promoter pledge at 80%" in note for note in notes)
    assert "Gross NPA Threshold (HIGH)" in check_names
    assert any("Gross NPA at 12%" in note for note in notes)


def test_cross_verify_adds_medium_flags_for_threshold_breaches() -> None:
    case = Case(id="case-medium-flags", company_name="Medium Risk Co", cin="L65922RJ2011PLC034297")
    share_doc = _document("share-2", "Shareholding_Pattern")
    portfolio_doc = _document("portfolio-2", "Portfolio_Performance")

    checks = cross_verify(
        case,
        [],
        [
            _extraction(share_doc, "shares_pledged_percent", numeric="60"),
            _extraction(portfolio_doc, "gnpa_percent", numeric="6.5"),
        ],
    )

    check_names = {check["check_name"] for check in checks}
    notes = {check["note"] for check in checks}

    assert "Promoter Pledge Threshold (MEDIUM)" in check_names
    assert any("Promoter pledge at 60%" in note for note in notes)
    assert "Gross NPA Threshold (MEDIUM)" in check_names
    assert any("Gross NPA at 6.5%" in note for note in notes)
