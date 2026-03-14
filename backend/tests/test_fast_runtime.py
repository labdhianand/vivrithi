import asyncio
from pathlib import Path

import pytest

from backend.app.config import get_settings
from backend.app.services.runtime.native import parse_document_native
from backend.app.services.runtime.pipeline import FastDocumentPipeline


@pytest.fixture(autouse=True)
def disable_gemini(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_parse_document_native_captures_geometry_and_routes() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")

    result = parse_document_native(pdf_path, max_workers=2)

    assert result.page_count == 2
    assert result.route_counts["native_table"] >= 1
    assert result.content_type_counts["financial_table"] >= 1
    assert result.pages[0].tokens
    assert result.pages[0].lines
    assert result.pages[0].tables


def test_fast_pipeline_extracts_expected_alm_fields() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")

    result = asyncio.run(FastDocumentPipeline(max_workers=2).run(pdf_path, forced_category="ALM"))
    values = result.active_values()

    assert result.classification_category == "ALM"
    assert values["lcr_ratio"] == "151.7%"
    assert values["hqla_total_weighted"] == "23,203"
    assert values["total_net_cash_outflows"] == "15,291"


def test_fast_pipeline_extracts_expected_shareholding_fields() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/Shareholding_Pattern/Shareholding_Pattern_Q3_FY26.pdf")

    result = asyncio.run(
        FastDocumentPipeline(max_workers=4, full_doc_fallback_threshold=3).run(
            pdf_path,
            forced_category="Shareholding_Pattern",
        )
    )
    values = result.active_values()

    assert values["promoter_holding_percent"] == "48.95%"
    assert values["public_holding_percent"] == "51.05%"
    assert values["fpi_holding_percent"] == "24.72%"
    assert values["promoter_name"].rstrip(".") == "Aquilo House Pte. Ltd"


def test_fast_pipeline_extracts_expected_borrowing_fields() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/Borrowing_Profile/Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf")

    result = asyncio.run(
        FastDocumentPipeline(max_workers=4, full_doc_fallback_threshold=4).run(
            pdf_path,
            forced_category="Borrowing_Profile",
        )
    )
    values = result.active_values()

    assert values["rating_agency"] == "CARE Ratings Limited"
    assert values["long_term_rating"] == "CARE AA"
    assert values["long_term_outlook"] == "Stable"
    assert values["rating_action"] == "Reaffirmed"
    assert values["total_rated_facilities_crore"] == "9662.00"
