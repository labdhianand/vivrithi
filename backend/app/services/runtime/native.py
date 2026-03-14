from __future__ import annotations

import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

import fitz
import pdfplumber

from ..markdown_builder import build_document_markdown
from ..pdf_triage import _detect_scanned_page, classify_page_content
from ..utils import clean_text, table_to_markdown
from .types import FastDocumentParse, FastPageParse, GeometryBox, LineGeometry, TableGeometry, TokenGeometry


def _normalize_box(x1: float, y1: float, x2: float, y2: float, width: float, height: float) -> GeometryBox:
    safe_width = width or 1.0
    safe_height = height or 1.0
    return GeometryBox(
        x1=round(x1 / safe_width, 6),
        y1=round(y1 / safe_height, 6),
        x2=round(x2 / safe_width, 6),
        y2=round(y2 / safe_height, 6),
    )


def _group_lines(words: list[TokenGeometry], tolerance: float = 0.006) -> list[LineGeometry]:
    if not words:
        return []
    sorted_words = sorted(words, key=lambda item: (item.bbox.y1, item.bbox.x1))
    buckets: list[list[tuple[int, TokenGeometry]]] = []
    for index, word in enumerate(sorted_words):
        if not buckets:
            buckets.append([(index, word)])
            continue
        previous = buckets[-1][0][1]
        if abs(word.bbox.y1 - previous.bbox.y1) <= tolerance:
            buckets[-1].append((index, word))
        else:
            buckets.append([(index, word)])

    lines: list[LineGeometry] = []
    for bucket in buckets:
        ordered = sorted(bucket, key=lambda item: item[1].bbox.x1)
        text = clean_text(" ".join(item.text for _, item in ordered))
        if not text:
            continue
        x1 = min(item.bbox.x1 for _, item in ordered)
        y1 = min(item.bbox.y1 for _, item in ordered)
        x2 = max(item.bbox.x2 for _, item in ordered)
        y2 = max(item.bbox.y2 for _, item in ordered)
        lines.append(
            LineGeometry(
                text=text,
                bbox=GeometryBox(x1=x1, y1=y1, x2=x2, y2=y2),
                token_indices=[index for index, _ in ordered],
            )
        )
    return lines


def _merge_split_header_rows(rows: list[list[str | None]]) -> list[list[str | None]]:
    if len(rows) < 2:
        return rows
    merged: list[list[str | None]] = []
    skip_next = False
    for i in range(len(rows)):
        if skip_next:
            skip_next = False
            continue
        if i + 1 < len(rows):
            current = rows[i]
            next_row = rows[i + 1]
            current_filled = sum(1 for c in current if (c or "").strip())
            next_filled = sum(1 for c in next_row if (c or "").strip())
            width = max(len(current), len(next_row))
            if width > 1 and current_filled <= 1 and next_filled > current_filled:
                combined = []
                for j in range(width):
                    c1 = (current[j] if j < len(current) else "") or ""
                    c2 = (next_row[j] if j < len(next_row) else "") or ""
                    merged_cell = f"{c1.strip()} {c2.strip()}".strip()
                    combined.append(merged_cell or None)
                merged.append(combined)
                skip_next = True
                continue
        merged.append(rows[i])
    return merged


def _detect_and_reorder_columns(lines: list[LineGeometry], content_type: str) -> list[LineGeometry]:
    if content_type == "financial_table" or len(lines) < 4:
        return lines
    midpoint = 0.5
    gap_threshold = 0.05
    left = [line for line in lines if (line.bbox.x1 + line.bbox.x2) / 2 < midpoint - gap_threshold]
    right = [line for line in lines if (line.bbox.x1 + line.bbox.x2) / 2 > midpoint + gap_threshold]
    total = len(lines)
    if len(left) < total * 0.3 or len(right) < total * 0.3:
        return lines
    left_sorted = sorted(left, key=lambda l: l.bbox.y1)
    right_sorted = sorted(right, key=lambda l: l.bbox.y1)
    center = [line for line in lines if line not in left and line not in right]
    center_sorted = sorted(center, key=lambda l: l.bbox.y1)
    return left_sorted + right_sorted + center_sorted


def _route_page(text: str, is_scanned: bool, has_tables: bool, token_count: int) -> str:
    if not text.strip() and not is_scanned:
        return "skip"
    if is_scanned and has_tables:
        return "ocr_table"
    if is_scanned:
        return "ocr_text"
    if has_tables:
        return "native_table"
    if token_count < 8:
        return "skip"
    return "native_text"


def _parse_page_chunk(pdf_path: Path, page_numbers: list[int]) -> list[FastPageParse]:
    pages: list[FastPageParse] = []
    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber_pdf:
        for page_number in page_numbers:
            started = perf_counter()
            page_index = page_number - 1
            page = doc[page_index]
            plumber_page = plumber_pdf.pages[page_index]
            text = page.get_text("text") or ""
            width = float(page.rect.width or 1.0)
            height = float(page.rect.height or 1.0)
            try:
                tables = plumber_page.find_tables()
            except Exception:
                tables = []
            drawings = page.get_drawings()
            images = page.get_images()
            raw_dict = page.get_text("dict")
            font_names: set[str] = set()
            for block in raw_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line_item in block.get("lines", []):
                    for span in line_item.get("spans", []):
                        font_name = span.get("font", "")
                        if font_name:
                            font_names.add(font_name)
            words = []
            for word in plumber_page.extract_words():
                token_text = clean_text(word.get("text", ""))
                if not token_text:
                    continue
                words.append(
                    TokenGeometry(
                        text=token_text,
                        bbox=_normalize_box(
                            float(word["x0"]),
                            float(word["top"]),
                            float(word["x1"]),
                            float(word["bottom"]),
                            width,
                            height,
                        ),
                    )
                )
            lines = _group_lines(words)
            table_items: list[TableGeometry] = []
            markdown_parts = [clean_text(text)]
            for table in tables:
                rows = _merge_split_header_rows(table.extract())
                markdown = table_to_markdown(rows)
                markdown_parts.append(markdown)
                x1, y1, x2, y2 = table.bbox
                row_count = len(rows)
                column_count = max((len(row) for row in rows), default=0)
                table_items.append(
                    TableGeometry(
                        bbox=_normalize_box(float(x1), float(y1), float(x2), float(y2), width, height),
                        markdown=markdown,
                        row_count=row_count,
                        column_count=column_count,
                        rows=rows,
                    )
                )

            is_scanned = _detect_scanned_page(text, images, font_names, len(words))
            has_tables = bool(tables) or len(drawings) > 8
            content_type = classify_page_content(text, is_scanned, has_tables)
            lines = _detect_and_reorder_columns(lines, content_type)
            route = _route_page(text, is_scanned, has_tables, len(words))
            pages.append(
                FastPageParse(
                    page_number=page_number,
                    width=width,
                    height=height,
                    text=text,
                    markdown="\n\n".join(part for part in markdown_parts if part),
                    tokens=words,
                    lines=lines,
                    tables=table_items,
                    has_text_layer=len(words) >= 8,
                    has_tables=has_tables,
                    is_scanned=is_scanned,
                    content_type=content_type,
                    route=route,
                    parse_seconds=perf_counter() - started,
                )
            )
    return pages


def _chunk_page_numbers(page_count: int, max_workers: int) -> list[list[int]]:
    workers = max(1, min(max_workers, page_count))
    chunk_size = max(1, math.ceil(page_count / workers))
    page_numbers = list(range(1, page_count + 1))
    return [page_numbers[index : index + chunk_size] for index in range(0, page_count, chunk_size)]


def parse_document_native(pdf_path: Path, max_workers: int = 8) -> FastDocumentParse:
    started = perf_counter()
    with fitz.open(pdf_path) as doc:
        page_count = doc.page_count

    chunks = _chunk_page_numbers(page_count, max_workers=max_workers)
    pages: list[FastPageParse] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for batch in executor.map(lambda chunk: _parse_page_chunk(pdf_path, chunk), chunks):
            pages.extend(batch)

    pages.sort(key=lambda item: item.page_number)
    parsed_pages = [page.to_parsed_page() for page in pages]
    route_counts = Counter(page.route for page in pages)
    content_counts = Counter(page.content_type for page in pages)
    return FastDocumentParse(
        pdf_path=pdf_path,
        pages=pages,
        markdown=build_document_markdown(parsed_pages),
        parse_seconds=perf_counter() - started,
        page_count=page_count,
        route_counts=dict(route_counts),
        content_type_counts=dict(content_counts),
    )
