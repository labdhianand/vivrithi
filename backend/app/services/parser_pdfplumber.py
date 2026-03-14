from __future__ import annotations

from pathlib import Path

import pdfplumber

from .types import ParsedPage, ParsedTable
from .utils import clean_text, table_to_markdown


def normalize_bbox(bbox: tuple[float, float, float, float], width: float, height: float) -> tuple[float, float, float, float]:
    x0, top, x1, bottom = bbox
    return (
        round(x0 / width, 6),
        round(top / height, 6),
        round(x1 / width, 6),
        round(bottom / height, 6),
    )


def parse_page_pdfplumber(pdf_path: Path, page_num: int) -> ParsedPage:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        text = page.extract_text() or ""
        try:
            tables = page.find_tables()
        except Exception:
            tables = []
        table_results: list[ParsedTable] = []
        for table in tables:
            rows = table.extract()
            table_results.append(
                ParsedTable(
                    bbox=normalize_bbox(table.bbox, page.width, page.height),
                    rows=rows,
                    markdown=table_to_markdown(rows),
                )
            )
        markdown_parts = [clean_text(text)]
        markdown_parts.extend(table.markdown for table in table_results if table.markdown)
        word_boxes = []
        for word in page.extract_words():
            word_boxes.append(
                {
                    "text": word.get("text", ""),
                    "bbox": normalize_bbox(
                        (word["x0"], word["top"], word["x1"], word["bottom"]),
                        page.width,
                        page.height,
                    ),
                }
            )
        return ParsedPage(
            page_number=page_num + 1,
            text=text,
            markdown="\n\n".join(part for part in markdown_parts if part),
            tables=table_results,
            bounding_boxes=word_boxes,
            parser_used="pdfplumber",
            confidence=0.84 if text.strip() else 0.35,
        )

