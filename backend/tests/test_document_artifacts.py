import asyncio
from pathlib import Path

import pytest

from backend.app.config import get_settings
from backend.app.services.runtime import build_docling_artifact, build_fast_artifact


@pytest.fixture(autouse=True)
def disable_gemini(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fast_artifact_includes_pages_blocks_tables_and_chunks() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")

    artifact = asyncio.run(build_fast_artifact(pdf_path, category="ALM", max_workers=2))

    assert artifact.backend == "fast_runtime"
    assert artifact.page_count == 2
    assert artifact.pages
    assert artifact.text_blocks
    assert artifact.tables
    assert artifact.reading_order
    assert artifact.chunks
    assert artifact.raw_exports["field_values"]["lcr_ratio"] == "151.7%"


def test_docling_artifact_includes_docling_exports_tables_and_chunks() -> None:
    pdf_path = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")

    artifact = build_docling_artifact(pdf_path)

    assert artifact.backend == "docling"
    assert artifact.page_count == 2
    assert artifact.pages
    assert artifact.text_blocks
    assert artifact.tables
    assert artifact.chunks
    assert "dict" in artifact.raw_exports
    assert "html" in artifact.raw_exports
    assert "doctags" in artifact.raw_exports
    assert "document_tokens" in artifact.raw_exports
    assert artifact.tables[0].cells
