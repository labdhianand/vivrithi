from pathlib import Path

from backend.app.services.pdf_triage import triage_document


def test_triage_document_detects_financial_table() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")

    results = triage_document(pdf_path, "case-test", "doc-test")

    assert len(results) == 2
    assert results[0].has_tables is True
    assert results[0].content_type == "financial_table"
    assert results[1].content_type in {"narrative", "financial_table"}

