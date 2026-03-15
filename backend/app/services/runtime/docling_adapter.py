from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from .docling_remote import build_marker_payload_sync, convert_pdf_to_markdown_sync


@dataclass(slots=True)
class DoclingResult:
    markdown: str
    text: str
    page_count: int
    convert_seconds: float
    document: Any


class DoclingBackend:
    def convert(self, pdf_path: Path) -> DoclingResult:
        started = perf_counter()
        conversion = convert_pdf_to_markdown_sync(str(pdf_path))
        payload = build_marker_payload_sync(str(pdf_path), conversion)
        elapsed = perf_counter() - started
        payload["convert_seconds"] = round(elapsed, 6)
        return DoclingResult(
            markdown=payload.get("markdown", ""),
            text=payload.get("text", ""),
            page_count=int(payload.get("page_count") or 0),
            convert_seconds=elapsed,
            document=payload,
        )
