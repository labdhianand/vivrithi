from __future__ import annotations

import asyncio
from pathlib import Path

import fitz

from backend.app.services.classifier import classify_document


def _first_pages_markdown(pdf_path: Path, page_count: int = 3) -> str:
    with fitz.open(pdf_path) as doc:
        parts = []
        for index in range(min(page_count, doc.page_count)):
            parts.append(doc[index].get_text("text", sort=True))
    return "\n\n".join(parts)


def test_classify_sample_documents_from_corpus() -> None:
    corpus = [
        (
            Path("data/challenge_doc_corpus/raw/ALM/mid/Aavas_Financiers/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf"),
            "ALM",
        ),
        (
            Path("data/challenge_doc_corpus/raw/Shareholding_Pattern/mid/Aavas_Financiers/Shareholding_Pattern_Q3_FY26.pdf"),
            "Shareholding_Pattern",
        ),
        (
            Path("data/challenge_doc_corpus/raw/Borrowing_Profile/mid/Aavas_Financiers/Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf"),
            "Borrowing_Profile",
        ),
        (
            Path("data/challenge_doc_corpus/raw/Annual_Report/mid/Aavas_Financiers/Annual_Report_FY2024-25.pdf"),
            "Annual_Report",
        ),
        (
            Path("data/challenge_doc_corpus/raw/Portfolio_Cuts_Performance/mid/Aavas_Financiers/Financial_Result_Q3_FY26.pdf"),
            "Portfolio_Performance",
        ),
    ]
    for pdf_path, expected in corpus:
        markdown = _first_pages_markdown(pdf_path)
        result = asyncio.run(classify_document(markdown, filename=pdf_path.name))
        assert result.category == expected, f"{pdf_path.name}: {result}"


def test_classify_document_falls_back_when_llm_confidence_is_invalid(monkeypatch) -> None:
    async def _run() -> None:
        monkeypatch.setattr("backend.app.services.classifier.has_text_llm", lambda: True)
        monkeypatch.setattr(
            "backend.app.services.classifier.generate_json",
            lambda *args, **kwargs: {
                "category": "Portfolio_Performance",
                "confidence": "moderate",
                "reasoning": "bad confidence shape",
            },
        )
        result = await classify_document(
            "Shareholding Pattern\nRegulation 31\nPromoter and promoter group",
            filename="Shareholding_Pattern_Q3_FY26.pdf",
        )
        assert result.category == "Shareholding_Pattern"

    asyncio.run(_run())


def test_classify_document_falls_back_when_llm_raises(monkeypatch) -> None:
    async def _run() -> None:
        monkeypatch.setattr("backend.app.services.classifier.has_text_llm", lambda: True)

        def _raise(*args, **kwargs):
            raise RuntimeError("quota exceeded")

        monkeypatch.setattr("backend.app.services.classifier.generate_json", _raise)
        result = await classify_document(
            "Unaudited Financial Results\nOutcome of the Board Meeting\nGross NPA",
            filename="Financial_Result_Q3_FY26.pdf",
        )
        assert result.category == "Portfolio_Performance"

    asyncio.run(_run())
