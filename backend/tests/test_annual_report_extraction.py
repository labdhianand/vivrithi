from __future__ import annotations

from pathlib import Path

import fitz

from backend.app.extraction_schemas.annual_report import ANNUAL_REPORT_DEFAULT_SCHEMA
from backend.app.services.extractor import _infer_value
from backend.app.services.runtime.native import _parse_page_chunk


def _page_lines(pdf_path: Path, page_numbers: list[int]) -> dict[int, list[str]]:
    page_lines: dict[int, list[str]] = {}
    with fitz.open(pdf_path) as doc:
        for page_number in page_numbers:
            text = doc[page_number - 1].get_text("text", sort=True)
            page_lines[page_number] = [line.strip() for line in text.splitlines() if line.strip()]
    return page_lines


def test_annual_report_pattern_recovery_for_core_fields() -> None:
    pdf_path = Path("data/challenge_doc_corpus/raw/Annual_Report/mid/Aavas_Financiers/Annual_Report_FY2024-25.pdf")
    page_lines = _page_lines(pdf_path, [7, 8, 23, 30, 31, 78, 79, 93, 94])
    field_map = {field["key"]: field for field in ANNUAL_REPORT_DEFAULT_SCHEMA["fields"]}

    expectations = {
        "fiscal_year": "2024-25",
        "aum_crore": "20,420",
        "net_worth_crore": "4,361",
        "total_revenue_crore": "2,358",
        "pat_crore": "574",
        "disbursements_crore": "6,123",
        "roe_percent": "14.12%",
        "roa_percent": "3.27%",
        "nim_percent": "7.64%",
        "branch_count": "397",
        "states_present": "14",
        "housing_loan_percent": "68%",
        "non_housing_loan_percent": "32%",
        "auditor_name": "M S K A & Associates / Borkar & Muzumdar",
    }

    for field_key, expected_value in expectations.items():
        value, page_number, confidence, method = _infer_value(field_map[field_key], page_lines)
        assert value == expected_value, (field_key, value, page_number, confidence, method)
        assert page_number is not None
        assert confidence >= 0.9


def test_annual_report_runtime_page_shapes_recover_core_fields() -> None:
    pdf_path = Path("data/challenge_doc_corpus/raw/Annual_Report/mid/Aavas_Financiers/Annual_Report_FY2024-25.pdf")
    pages = _parse_page_chunk(pdf_path, [7, 8, 78, 79, 93, 94])
    page_lines = {page.page_number: [line.strip() for line in page.markdown.splitlines() if line.strip()] for page in pages}
    field_map = {field["key"]: field for field in ANNUAL_REPORT_DEFAULT_SCHEMA["fields"]}

    expectations = {
        "aum_crore": "20,420",
        "net_worth_crore": "4,361",
        "total_revenue_crore": "2,358",
        "pat_crore": "574",
        "disbursements_crore": "6,123",
        "roe_percent": "14.12%",
        "roa_percent": "3.27%",
        "nim_percent": "7.64%",
        "spread_percent": "4.98%",
        "eps": "72.54",
        "branch_count": "397",
        "employee_count": "7,233",
        "states_present": "14",
        "housing_loan_percent": "68%",
        "non_housing_loan_percent": "32%",
        "auditor_name": "M S K A & Associates / Borkar & Muzumdar",
    }

    for field_key, expected_value in expectations.items():
        value, page_number, confidence, method = _infer_value(field_map[field_key], page_lines)
        assert value == expected_value, (field_key, value, page_number, confidence, method)
        assert page_number is not None
        assert confidence >= 0.9
