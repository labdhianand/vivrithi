from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import httpx
import pdfplumber

from ...config import get_settings
from ..types import ParsedPage, ParsedTable


logger = logging.getLogger(__name__)
TIMEOUT = 120


@dataclass(slots=True)
class RemoteDoclingResult:
    markdown: str
    text: str
    page_count: int
    convert_seconds: float
    payload: dict[str, Any]


def _marker_url() -> str:
    return get_settings().marker_api_url.rstrip("/")


def _table_markdown(rows: list[list[str | None]]) -> str:
    if not rows:
        return ""
    width = max((len(row) for row in rows), default=0)
    normalized = [
        [(cell or "").strip() for cell in row] + [""] * (width - len(row))
        for row in rows
    ]
    if not normalized:
        return ""
    lines = [
        "| " + " | ".join(normalized[0]) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _table_cells(rows: list[list[str | None]]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            if value in (None, ""):
                continue
            cells.append(
                {
                    "row_index": row_index,
                    "column_index": column_index,
                    "text": str(value),
                    "bbox": None,
                }
            )
    return cells


def build_marker_payload_sync(
    file_path: str,
    conversion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conversion = conversion or {}
    document_markdown = conversion.get("markdown") or ""
    backend_name = str(conversion.get("method") or conversion.get("backend") or "marker_api")

    pages: list[dict[str, Any]] = []
    text_blocks: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    combined_text_parts: list[str] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = (page.extract_text() or "").strip()
                if page_text:
                    combined_text_parts.append(page_text)

                page_tables: list[dict[str, Any]] = []
                for table_index, raw_rows in enumerate(page.extract_tables() or []):
                    rows = [[cell if cell is None else str(cell) for cell in row] for row in raw_rows]
                    markdown = _table_markdown(rows)
                    table_payload = {
                        "table_id": f"p{page_number}-table-{table_index}",
                        "page_number": page_number,
                        "bbox": None,
                        "markdown": markdown,
                        "row_count": len(rows),
                        "column_count": max((len(row) for row in rows), default=0),
                        "rows": rows,
                        "cells": _table_cells(rows),
                        "source_engine": backend_name,
                    }
                    tables.append(table_payload)
                    page_tables.append(
                        {
                            "bbox": None,
                            "rows": rows,
                            "markdown": markdown,
                            "sheet_name": None,
                        }
                    )

                text_lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                for line_index, line in enumerate(text_lines):
                    text_blocks.append(
                        {
                            "block_id": f"p{page_number}-line-{line_index}",
                            "page_number": page_number,
                            "label": "text",
                            "text": line,
                            "bbox": None,
                            "reading_order_index": len(text_blocks),
                            "source_engine": backend_name,
                        }
                    )

                page_markdown_parts = [page_text] if page_text else []
                page_markdown_parts.extend(
                    table["markdown"] for table in page_tables if table.get("markdown")
                )
                pages.append(
                    {
                        "page_number": page_number,
                        "width": float(page.width),
                        "height": float(page.height),
                        "has_tables": bool(page_tables),
                        "text": page_text,
                        "markdown": "\n\n".join(page_markdown_parts).strip(),
                        "tables": page_tables,
                        "bounding_boxes": [],
                        "parser_used": backend_name,
                        "route": backend_name,
                    }
                )
    except Exception as exc:
        logger.warning("Structured pdfplumber pass failed for %s: %s", file_path, exc)

    if not pages and document_markdown:
        synthetic_text = document_markdown.strip()
        pages.append(
            {
                "page_number": 1,
                "width": 1.0,
                "height": 1.0,
                "has_tables": False,
                "text": synthetic_text,
                "markdown": synthetic_text,
                "tables": [],
                "bounding_boxes": [],
                "parser_used": backend_name,
                "route": backend_name,
            }
        )
        for line_index, line in enumerate(
            [line.strip() for line in synthetic_text.splitlines() if line.strip()]
        ):
            text_blocks.append(
                {
                    "block_id": f"p1-line-{line_index}",
                    "page_number": 1,
                    "label": "text",
                    "text": line,
                    "bbox": None,
                    "reading_order_index": len(text_blocks),
                    "source_engine": backend_name,
                }
            )

    combined_text = "\n\n".join(part for part in combined_text_parts if part).strip()
    return {
        "backend": backend_name,
        "document_name": Path(file_path).name,
        "source_path": file_path,
        "page_count": len(pages),
        "markdown": document_markdown or combined_text,
        "text": combined_text or document_markdown,
        "pages": pages,
        "text_blocks": text_blocks,
        "tables": tables,
        "metadata": conversion.get("metadata") or {},
        "error": conversion.get("error") or "",
    }


async def convert_pdf_to_markdown(file_path: str) -> dict[str, Any]:
    """
    Primary path: send PDF to Marker on GPU via tunnel.
    Returns clean markdown preserving tables and structure.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            with open(file_path, "rb") as file_handle:
                response = await client.post(
                    f"{_marker_url()}/convert",
                    files={
                        "pdf_file": (
                            Path(file_path).name,
                            file_handle,
                            "application/pdf",
                        )
                    },
                )
        if response.status_code == 200:
            data = response.json()
            if data.get("success", True):
                return {
                    "markdown": data.get("markdown", ""),
                    "method": "marker_api",
                    "success": True,
                    "pages": [],
                    "metadata": {},
                }
            raise RuntimeError(data.get("error") or "Marker conversion failed")
        raise RuntimeError(f"Marker returned HTTP {response.status_code}")
    except Exception as exc:
        logger.warning("Marker unavailable (%s), using pdfplumber fallback", exc)
        return await _pdfplumber_fallback(file_path, str(exc))


async def _pdfplumber_fallback(
    file_path: str,
    error: str = "",
) -> dict[str, Any]:
    """
    Fallback when Marker tunnel is down.
    Extracts text and tables using pdfplumber.
    """

    def _extract() -> tuple[str, list[Any]]:
        pages_text: list[str] = []
        tables: list[Any] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                    page_tables = page.extract_tables() or []
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as exc:
            logger.error("pdfplumber fallback failed for %s: %s", file_path, exc)
        return "\n\n".join(pages_text), tables

    text, tables = await asyncio.to_thread(_extract)
    return {
        "markdown": text,
        "method": "pdfplumber_fallback",
        "success": bool(text),
        "pages": [],
        "metadata": {"tables": tables},
        "error": error,
    }


def convert_pdf_to_markdown_sync(file_path: str) -> dict[str, Any]:
    return asyncio.run(convert_pdf_to_markdown(file_path))


async def get_first_page_text(file_path: str) -> str:
    """
    Fast first-page extraction for classification only.
    Uses pdfplumber and never calls Marker.
    """

    def _extract() -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                if pdf.pages:
                    return (pdf.pages[0].extract_text() or "").strip()
        except Exception:
            return ""
        return ""

    return await asyncio.to_thread(_extract)


async def check_marker_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{_marker_url()}/health")
            return response.status_code == 200
    except Exception:
        return False


class DoclingRemoteBackend:
    async def convert(self, source_path: Path) -> RemoteDoclingResult:
        started = perf_counter()
        conversion = await convert_pdf_to_markdown(str(source_path))
        payload = await asyncio.to_thread(
            build_marker_payload_sync,
            str(source_path),
            conversion,
        )
        elapsed = perf_counter() - started
        payload["convert_seconds"] = round(elapsed, 6)
        return RemoteDoclingResult(
            markdown=payload.get("markdown", ""),
            text=payload.get("text", ""),
            page_count=int(payload.get("page_count") or 0),
            convert_seconds=elapsed,
            payload=payload,
        )


def parsed_pages_from_remote_payload(payload: dict[str, Any]) -> list[ParsedPage]:
    parsed_pages: list[ParsedPage] = []
    for page in payload.get("pages", []):
        tables = [
            ParsedTable(
                bbox=tuple(table.get("bbox") or [0.0, 0.0, 1.0, 1.0]),
                rows=table.get("rows") or [],
                markdown=table.get("markdown") or "",
                sheet_name=table.get("sheet_name"),
            )
            for table in page.get("tables", [])
        ]
        parsed_pages.append(
            ParsedPage(
                page_number=int(page["page_number"]),
                text=page.get("text") or "",
                markdown=page.get("markdown") or "",
                tables=tables,
                bounding_boxes=page.get("bounding_boxes") or [],
                parser_used=page.get("parser_used") or page.get("route") or "docling_gpu_remote",
                confidence=0.94 if payload.get("backend") == "marker_api" else 0.78,
            )
        )
    return parsed_pages


_remote_backend: DoclingRemoteBackend | None = None


def get_docling_remote_backend() -> DoclingRemoteBackend:
    global _remote_backend
    if _remote_backend is None:
        _remote_backend = DoclingRemoteBackend()
    return _remote_backend
