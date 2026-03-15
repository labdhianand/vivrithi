import asyncio
from pathlib import Path

import pytest

from backend.app.extraction_schemas.alm import ALM_DEFAULT_SCHEMA
from backend.app.extraction_schemas.borrowing import BORROWING_DEFAULT_SCHEMA
from backend.app.extraction_schemas.shareholding import SHAREHOLDING_DEFAULT_SCHEMA
from backend.app.services import extractor
from backend.app.services.extractor import extract_with_schema
from backend.app.services.markdown_builder import build_document_markdown
from backend.app.services.parser_pdfplumber import parse_page_pdfplumber
from backend.app.services.types import ParsedPage, ParsedTable


def test_alm_extraction_hits_expected_lcr_fields() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")
    pages = [parse_page_pdfplumber(pdf_path, 0), parse_page_pdfplumber(pdf_path, 1)]

    results = asyncio.run(extract_with_schema(pdf_path, build_document_markdown(pages), ALM_DEFAULT_SCHEMA, pages))
    result_map = {item.key: item for item in results}

    assert result_map["lcr_ratio"].value == "151.7%"
    assert result_map["hqla_total_weighted"].value == "23,203"
    assert result_map["total_net_cash_outflows"].value == "15,291"


def test_shareholding_extraction_hits_expected_summary_values() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/Shareholding_Pattern/Shareholding_Pattern_Q3_FY26.pdf")
    pages = [parse_page_pdfplumber(pdf_path, index) for index in range(8)]

    results = asyncio.run(
        extract_with_schema(
            pdf_path,
            build_document_markdown(pages),
            SHAREHOLDING_DEFAULT_SCHEMA,
            pages,
        )
    )
    result_map = {item.key: item for item in results}

    assert result_map["promoter_holding_percent"].value == "48.95%"
    assert result_map["public_holding_percent"].value == "51.05%"
    assert result_map["fpi_holding_percent"].value == "24.72%"
    assert result_map["promoter_name"].value == "Aquilo House Pte. Ltd"


def test_borrowing_profile_extraction_hits_core_rating_fields() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/Borrowing_Profile/Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf")
    pages = [parse_page_pdfplumber(pdf_path, index) for index in range(10)]

    results = asyncio.run(
        extract_with_schema(
            pdf_path,
            build_document_markdown(pages),
            BORROWING_DEFAULT_SCHEMA,
            pages,
        )
    )
    result_map = {item.key: item for item in results}

    assert result_map["rating_agency"].value == "CARE Ratings Limited"
    assert result_map["long_term_rating"].value == "CARE AA"
    assert result_map["long_term_outlook"].value == "Stable"
    assert result_map["rating_action"].value == "Reaffirmed"
    assert result_map["total_rated_facilities_crore"].value == "9662.00"


def test_extraction_falls_back_when_llm_returns_null_value(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_llm_extract(document_markdown: str, schema: dict, pages=None) -> list[dict]:
        return [{"key": "fpi_holding_percent", "value": None, "value_numeric": None, "page_number": 4, "confidence": None}]

    monkeypatch.setattr(extractor, "_llm_extract", fake_llm_extract)

    pdf_path = Path("claude_data/Aavas_Financiers/Shareholding_Pattern/Shareholding_Pattern_Q3_FY26.pdf")
    pages = [parse_page_pdfplumber(pdf_path, index) for index in range(8)]

    results = asyncio.run(
        extract_with_schema(
            pdf_path,
            build_document_markdown(pages),
            SHAREHOLDING_DEFAULT_SCHEMA,
            pages,
        )
    )
    result_map = {item.key: item for item in results}

    assert result_map["fpi_holding_percent"].value == "24.72%"


def test_priority_heuristics_override_conflicting_llm_value(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_llm_extract(document_markdown: str, schema: dict, pages=None) -> list[dict]:
        return [
            {
                "key": "total_rated_facilities_crore",
                "value": "10,905.40",
                "value_numeric": "10905.40",
                "page_number": 1,
                "confidence": 0.75,
            }
        ]

    monkeypatch.setattr(extractor, "_llm_extract", fake_llm_extract)

    pdf_path = Path("claude_data/Aavas_Financiers/Borrowing_Profile/Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf")
    pages = [parse_page_pdfplumber(pdf_path, index) for index in range(10)]

    results = asyncio.run(
        extract_with_schema(
            pdf_path,
            build_document_markdown(pages),
            BORROWING_DEFAULT_SCHEMA,
            pages,
        )
    )
    result_map = {item.key: item for item in results}

    assert result_map["total_rated_facilities_crore"].value == "9662.00"
    assert result_map["total_rated_facilities_crore"].extraction_method == "borrowing_summary"


def test_alm_extraction_keeps_blank_rows_missing_instead_of_guessing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_llm_extract(document_markdown: str, schema: dict, pages=None) -> list[dict] | None:
        return None

    monkeypatch.setattr(extractor, "_llm_extract", fake_llm_extract)

    rows = [
        ["Appendix I", None, None, None, None],
        ["(in lakhs)", None, "Total Unweighted Value (average)", "Total Weighted Value (average)", None],
        ["1", "Total High Quality Liquid Assets (HQLA)", "34,636.37", "34,636.37", None],
        ["2", "Deposits (for deposit taking companies)", "-", "-", None],
        ["3", "Unsecured wholesale funding", "-", "-", None],
        ["4", "Secured funding", "18,800.09", "21,620.11", None],
        ["(iii)", "Credit and liquidity facilities", "-", "-", None],
        ["6", "Other contractual funding obligations", "53,074.71", "61,035.91", None],
        ["7", "Other contingent funding obligations", "-", "-", None],
        ["8", "Total Cash Outflows", "71,874.80", "82,656.02", None],
        ["9", "Secured Lending", "15,700.17", "11,775.13", None],
        ["10", "Inflows from fully performing exposures", "-", "-", None],
        ["11", "Other cash inflows", "2,70,210.58", "2,02,657.94", None],
        ["12", "TOTAL CASH INFLOWS", "2,85,910.75", "2,14,433.06", None],
        ["14", "TOTAL NET CASH OUTFLOWS", None, "20,664.00", None],
        ["15", "LIQUIDITY COVERAGE RATIO (%) *", None, "167.62%", None],
    ]
    page = ParsedPage(
        page_number=1,
        text="Home First Finance Company India Limited LCR disclosure for quarter ended December 31, 2025",
        markdown="",
        tables=[ParsedTable(bbox=(0.0, 0.0, 1.0, 1.0), rows=rows, markdown="")],
        bounding_boxes=[],
    )

    results = asyncio.run(
        extract_with_schema(
            pdf_path=Path("synthetic.txt"),
            document_markdown=build_document_markdown([page]),
            schema=ALM_DEFAULT_SCHEMA,
            pages=[page],
        )
    )
    result_map = {item.key: item for item in results}

    assert result_map["hqla_total_weighted"].value == "34,636.37"
    assert result_map["cash_outflow_secured_wholesale"].value == "21,620.11"
    assert result_map["cash_outflow_other_contractual"].value == "61,035.91"
    assert result_map["cash_inflow_secured_lending"].value == "11,775.13"
    assert result_map["cash_inflow_other"].value == "2,02,657.94"
    assert result_map["total_cash_outflows_weighted"].value == "82,656.02"
    assert result_map["total_net_cash_outflows"].value == "20,664.00"
    assert result_map["lcr_ratio"].value == "167.62%"

    assert result_map["cash_outflow_deposits"].value is None
    assert result_map["cash_outflow_deposits"].extraction_method == "table_blank"
    assert result_map["cash_outflow_credit_facilities"].value is None
    assert result_map["cash_outflow_credit_facilities"].extraction_method == "table_blank"
    assert result_map["cash_inflow_performing_exposures"].value is None
    assert result_map["cash_inflow_performing_exposures"].extraction_method == "table_blank"
