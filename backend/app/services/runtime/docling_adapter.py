from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

try:
    from docling.document_converter import DocumentConverter
except ImportError:  # pragma: no cover - optional dependency
    DocumentConverter = None


@dataclass(slots=True)
class DoclingResult:
    markdown: str
    text: str
    page_count: int
    convert_seconds: float
    document: Any


class DoclingBackend:
    def __init__(self) -> None:
        if DocumentConverter is None:
            raise RuntimeError("docling is not installed")
        self.converter = DocumentConverter()

    def convert(self, pdf_path: Path) -> DoclingResult:
        started = perf_counter()
        result = self.converter.convert(pdf_path)
        elapsed = perf_counter() - started
        document = result.document
        return DoclingResult(
            markdown=document.export_to_markdown(),
            text=document.export_to_text(),
            page_count=len(document.pages),
            convert_seconds=elapsed,
            document=document,
        )
