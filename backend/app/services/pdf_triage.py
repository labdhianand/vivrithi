from __future__ import annotations

from pathlib import Path

import fitz
import pdfplumber

from .storage import storage
from .types import PageTriageResult


def _detect_scanned_page(
    text: str,
    images: list,
    font_names: set[str] | None = None,
    word_count: int = 0,
) -> bool:
    text_len = len(text.strip())
    has_images = len(images) > 0
    if word_count < 8 and text_len < 40 and has_images:
        return True
    if not has_images:
        return False
    if font_names is not None and len(font_names) == 1 and has_images and word_count > 0:
        return True
    return False


def classify_page_content(text: str, is_scanned: bool, has_tables: bool) -> str:
    normalized = text.lower()
    stripped = normalized.strip()
    if not stripped:
        return "blank"
    if "dear sir" in normalized or "to the national stock exchange" in normalized:
        return "cover_letter"
    if any(token in normalized for token in ["signatory", "signature", "sd/-"]) and len(stripped) < 200:
        return "signature_page"
    if any(phrase in normalized for phrase in [
        "notes to the financial statements",
        "notes forming part of",
        "significant accounting policies",
    ]):
        return "notes_to_accounts"
    if any(phrase in normalized for phrase in [
        "directors' report",
        "directors\u2019 report",
        "board's report",
        "board\u2019s report",
        "report of the board",
    ]):
        return "directors_report"
    if any(phrase in normalized for phrase in [
        "regulatory disclosure",
        "disclosure under",
        "rbi circular",
        "master direction",
    ]):
        return "regulatory_disclosure"
    if has_tables:
        return "financial_table"
    if is_scanned and len(stripped) < 50:
        return "chart_or_infographic"
    if len(stripped) < 20:
        return "blank"
    return "narrative"


def triage_document(pdf_path: Path, case_id: str, document_id: str) -> list[PageTriageResult]:
    results: list[PageTriageResult] = []
    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber_pdf:
        for index, page in enumerate(doc):
            page_number = index + 1
            text = page.get_text("text")
            plumber_page = plumber_pdf.pages[index]
            try:
                table_candidates = plumber_page.find_tables()
            except Exception:
                table_candidates = []
            drawings = page.get_drawings()
            has_tables = bool(table_candidates) or len(drawings) > 8
            images = page.get_images()
            raw_dict = page.get_text("dict")
            font_names: set[str] = set()
            for block in raw_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_name = span.get("font", "")
                        if font_name:
                            font_names.add(font_name)
            word_count = len(text.split())
            is_scanned = _detect_scanned_page(text, images, font_names, word_count)
            content_type = classify_page_content(text, is_scanned, has_tables)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            relative_image_path = storage.save_page_image(
                case_id=case_id,
                document_id=document_id,
                page_number=page_number,
                image_bytes=pixmap.tobytes("png"),
            )
            results.append(
                PageTriageResult(
                    page_number=page_number,
                    is_scanned=is_scanned,
                    has_tables=has_tables,
                    content_type=content_type,
                    text_content=text,
                    image_path=relative_image_path,
                )
            )
    return results

