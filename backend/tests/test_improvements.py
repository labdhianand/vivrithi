"""Unit tests for the 10 Docling FastFork improvements."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services import extractor
from backend.app.services.extractor import extract_with_schema
from backend.app.services.pdf_triage import _detect_scanned_page, classify_page_content
from backend.app.services.utils import table_to_markdown


# ---------------------------------------------------------------------------
# Improvement 1: Smarter Scanned Page Detection
# ---------------------------------------------------------------------------


def test_detect_scanned_page_single_font() -> None:
    """Single font + images → scanned (OCR overlay)."""
    assert _detect_scanned_page(
        text="Some OCR text here on page",
        images=["img1.png"],
        font_names={"ArialMT"},
        word_count=20,
    ) is True


def test_detect_scanned_page_multi_font() -> None:
    """Multiple fonts + images → not scanned (real PDF)."""
    assert _detect_scanned_page(
        text="Some styled text here on page",
        images=["img1.png"],
        font_names={"ArialMT", "TimesNewRoman", "Helvetica-Bold"},
        word_count=20,
    ) is False


def test_detect_scanned_page_no_images() -> None:
    """No images → never scanned."""
    assert _detect_scanned_page(
        text="x",
        images=[],
        font_names={"ArialMT"},
        word_count=2,
    ) is False


def test_detect_scanned_page_classic() -> None:
    """Few words + short text + images → scanned (classic heuristic)."""
    assert _detect_scanned_page(
        text="  ",
        images=["img1.png"],
        font_names=set(),
        word_count=3,
    ) is True


# ---------------------------------------------------------------------------
# Improvement 2: Merge Split Header Rows
# ---------------------------------------------------------------------------


def test_merge_split_header_rows() -> None:
    from backend.app.services.runtime.native import _merge_split_header_rows

    # First row has only 1 filled cell (sparse), second row has content in same positions
    rows = [
        ["Category", "", "", ""],
        ["", "Q1", "Q2", "Q3"],
        ["Revenue", "10", "20", "30"],
    ]
    merged = _merge_split_header_rows(rows)
    assert len(merged) == 2
    assert merged[0][0] == "Category"
    assert merged[0][1] == "Q1"


def test_merge_split_header_rows_no_merge() -> None:
    from backend.app.services.runtime.native import _merge_split_header_rows

    rows = [
        ["A", "B", "C"],
        ["1", "2", "3"],
    ]
    merged = _merge_split_header_rows(rows)
    assert len(merged) == 2
    assert merged[0] == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Improvement 7: Spanning Row Detection / Table-Aware Markdown
# ---------------------------------------------------------------------------


def test_spanning_row_detection_section_header() -> None:
    """Single-cell spanning row becomes bold section header."""
    rows = [
        ["Section A", "", "", ""],
        ["Col1", "Col2", "Col3", "Col4"],
        ["a", "b", "c", "d"],
    ]
    md = table_to_markdown(rows)
    assert "**Section A**" in md
    assert "| Col1 |" in md


def test_spanning_row_not_triggered_narrow_table() -> None:
    """Spanning row detection doesn't trigger for 2-column tables."""
    rows = [
        ["Header", ""],
        ["A", "B"],
    ]
    md = table_to_markdown(rows)
    assert "**" not in md


# ---------------------------------------------------------------------------
# Improvement 3: Semantic Chunking
# ---------------------------------------------------------------------------


def test_semantic_chunks_respect_tables() -> None:
    from experiments.docling_fastfork.docling.experimental.fastfork.artifacts import build_fast_chunks
    from experiments.docling_fastfork.docling.experimental.fastfork.types import ArtifactTable, ArtifactTextBlock, BBox

    blocks = [
        ArtifactTextBlock(
            block_id="b1", page_number=1, label="line", text="Intro text " * 20,
            bbox=BBox(0, 0, 1, 0.1), reading_order_index=0, source_engine="test",
        ),
        ArtifactTextBlock(
            block_id="b2", page_number=1, label="line", text="More text " * 20,
            bbox=BBox(0, 0.1, 1, 0.2), reading_order_index=1, source_engine="test",
        ),
    ]
    tables = [
        ArtifactTable(
            table_id="t1", page_number=1, bbox=BBox(0, 0.3, 1, 0.5),
            markdown="| A | B |\n| --- | --- |\n| 1 | 2 |",
            row_count=2, column_count=2, cells=[], source_engine="test",
        ),
    ]
    chunks = build_fast_chunks(blocks, tables=tables)
    table_chunks = [c for c in chunks if "| A |" in c.text]
    assert len(table_chunks) == 1
    assert table_chunks[0].text == "| A | B |\n| --- | --- |\n| 1 | 2 |"


def test_semantic_chunks_page_boundary() -> None:
    from experiments.docling_fastfork.docling.experimental.fastfork.artifacts import build_fast_chunks
    from experiments.docling_fastfork.docling.experimental.fastfork.types import ArtifactTextBlock, BBox

    blocks = [
        ArtifactTextBlock(
            block_id="b1", page_number=1, label="line", text="Page one text " * 30,
            bbox=BBox(0, 0, 1, 0.5), reading_order_index=0, source_engine="test",
        ),
        ArtifactTextBlock(
            block_id="b2", page_number=2, label="line", text="Page two text " * 10,
            bbox=BBox(0, 0, 1, 0.5), reading_order_index=1, source_engine="test",
        ),
    ]
    chunks = build_fast_chunks(blocks)
    page_numbers_per_chunk = [c.page_numbers for c in chunks]
    assert any(pn == [1] for pn in page_numbers_per_chunk)
    assert any(2 in pn for pn in page_numbers_per_chunk)


# ---------------------------------------------------------------------------
# Improvement 4: Multi-Column Reading Order
# ---------------------------------------------------------------------------


def test_column_reorder_two_column() -> None:
    from experiments.docling_fastfork.docling.experimental.fastfork.native import _detect_and_reorder_columns
    from experiments.docling_fastfork.docling.experimental.fastfork.types import BBox, TextBlockParse

    blocks = [
        TextBlockParse(text="Right top", bbox=BBox(0.6, 0.1, 0.9, 0.15), reading_order_index=0),
        TextBlockParse(text="Left top", bbox=BBox(0.05, 0.1, 0.4, 0.15), reading_order_index=1),
        TextBlockParse(text="Right bottom", bbox=BBox(0.6, 0.5, 0.9, 0.55), reading_order_index=2),
        TextBlockParse(text="Left bottom", bbox=BBox(0.05, 0.5, 0.4, 0.55), reading_order_index=3),
    ]
    reordered = _detect_and_reorder_columns(blocks, "narrative")
    texts = [b.text for b in reordered]
    assert texts.index("Left top") < texts.index("Left bottom")
    assert texts.index("Left bottom") < texts.index("Right top")
    assert texts.index("Right top") < texts.index("Right bottom")


def test_column_reorder_single_column() -> None:
    from experiments.docling_fastfork.docling.experimental.fastfork.native import _detect_and_reorder_columns
    from experiments.docling_fastfork.docling.experimental.fastfork.types import BBox, TextBlockParse

    blocks = [
        TextBlockParse(text="Line 1", bbox=BBox(0.1, 0.1, 0.9, 0.15), reading_order_index=0),
        TextBlockParse(text="Line 2", bbox=BBox(0.1, 0.2, 0.9, 0.25), reading_order_index=1),
        TextBlockParse(text="Line 3", bbox=BBox(0.1, 0.3, 0.9, 0.35), reading_order_index=2),
        TextBlockParse(text="Line 4", bbox=BBox(0.1, 0.4, 0.9, 0.45), reading_order_index=3),
    ]
    reordered = _detect_and_reorder_columns(blocks, "narrative")
    texts = [b.text for b in reordered]
    assert texts == ["Line 1", "Line 2", "Line 3", "Line 4"]


# ---------------------------------------------------------------------------
# Improvement 6: Confidence Cascade
# ---------------------------------------------------------------------------


def _make_dummy_pdf(tmp_path: Path) -> Path:
    """Create a minimal 1-page PDF for tests that call _search_bbox."""
    import fitz

    pdf_path = tmp_path / "dummy.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "Net interest margin 3.5%")
    page.insert_text((72, 120), "Rs. 5,000/- crore rated facilities")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_confidence_cascade_llm_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """LLM with 0.95 confidence beats heuristic with 0.7."""

    async def fake_llm_extract(document_markdown, schema, pages=None):
        return [
            {
                "key": "nim_percent",
                "value": "3.5%",
                "value_numeric": 3.5,
                "page_number": 1,
                "confidence": 0.95,
            }
        ]

    monkeypatch.setattr(extractor, "_llm_extract", fake_llm_extract)

    from backend.app.services.types import ParsedPage

    pdf_path = _make_dummy_pdf(tmp_path)
    pages = [
        ParsedPage(
            page_number=1,
            text="Net interest margin 3.5%",
            markdown="Net interest margin 3.5%",
            tables=[],
            bounding_boxes=[],
            parser_used="test",
            confidence=0.9,
        )
    ]
    schema = {"fields": [{"key": "nim_percent", "type": "percentage", "label": "Net Interest Margin"}]}
    results = asyncio.run(
        extract_with_schema(pdf_path, "Net interest margin 3.5%", schema, pages)
    )
    assert results[0].extraction_method == "gemini"


def test_confidence_cascade_heuristic_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Heuristic for priority field with boost beats LLM default confidence."""

    async def fake_llm_extract(document_markdown, schema, pages=None):
        return [
            {
                "key": "total_rated_facilities_crore",
                "value": "999",
                "value_numeric": 999,
                "page_number": 1,
                "confidence": 0.75,
            }
        ]

    monkeypatch.setattr(extractor, "_llm_extract", fake_llm_extract)

    from backend.app.services.types import ParsedPage

    pdf_path = _make_dummy_pdf(tmp_path)
    pages = [
        ParsedPage(
            page_number=1,
            text="Rs. 5,000/- crore rated facilities",
            markdown="Rs. 5,000/- crore rated facilities",
            tables=[],
            bounding_boxes=[],
            parser_used="test",
            confidence=0.9,
        )
    ]
    schema = {
        "fields": [
            {"key": "total_rated_facilities_crore", "type": "currency_crore", "label": "Total Rated Facilities"}
        ]
    }
    results = asyncio.run(
        extract_with_schema(pdf_path, "Rs. 5,000/- crore rated facilities", schema, pages)
    )
    assert results[0].extraction_method == "heuristic_rated_amount"


# ---------------------------------------------------------------------------
# Improvement 9: New Content Type Classification
# ---------------------------------------------------------------------------


def test_new_content_type_notes_to_accounts() -> None:
    text = "Notes to the financial statements for the year ended March 2024"
    assert classify_page_content(text, is_scanned=False, has_tables=False) == "notes_to_accounts"


def test_new_content_type_directors_report() -> None:
    text = "Directors' Report to the shareholders for FY 2023-24"
    assert classify_page_content(text, is_scanned=False, has_tables=False) == "directors_report"


def test_new_content_type_regulatory_disclosure() -> None:
    text = "Regulatory disclosure as per RBI circular dated 15-03-2024"
    assert classify_page_content(text, is_scanned=False, has_tables=False) == "regulatory_disclosure"


def test_content_type_preserves_existing() -> None:
    assert classify_page_content("", is_scanned=False, has_tables=False) == "blank"
    assert classify_page_content("Dear Sir", is_scanned=False, has_tables=False) == "cover_letter"
    assert classify_page_content("Some financial data here", is_scanned=False, has_tables=True) == "financial_table"
    assert classify_page_content("A normal paragraph with sufficient text for classification", is_scanned=False, has_tables=False) == "narrative"


# ---------------------------------------------------------------------------
# Improvement 10: LLM Prompt Contains Few-Shot
# ---------------------------------------------------------------------------


def test_llm_prompt_contains_few_shot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the prompt sent to LLM includes few-shot examples."""
    captured_prompts: list[str] = []

    def fake_generate_json(prompt: str, model: str = ""):
        captured_prompts.append(prompt)
        return []

    monkeypatch.setattr("backend.app.services.extractor.generate_json", fake_generate_json)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from backend.app.config import get_settings
    get_settings.cache_clear()
    try:
        schema = {"fields": [{"key": "lcr_ratio", "type": "percentage", "label": "LCR Ratio"}]}
        asyncio.run(extractor._llm_extract("Document text here", schema))
        assert captured_prompts
        prompt = captured_prompts[0]
        assert "Indian financial document" in prompt
        assert "lcr_ratio" in prompt
        assert "promoter_holding_percent" in prompt
        assert "DD-MM-YYYY" in prompt
    finally:
        get_settings.cache_clear()
