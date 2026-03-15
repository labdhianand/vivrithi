from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class PageTriageResult:
    page_number: int
    is_scanned: bool
    has_tables: bool
    content_type: str
    text_content: str
    image_path: str


@dataclass(slots=True)
class ParsedTable:
    bbox: tuple[float, float, float, float]
    rows: list[list[str | None]]
    markdown: str
    sheet_name: str | None = None


@dataclass(slots=True)
class ParsedPage:
    page_number: int
    text: str
    markdown: str
    tables: list[ParsedTable] = field(default_factory=list)
    bounding_boxes: list[dict] = field(default_factory=list)
    parser_used: str = "pdfplumber"
    confidence: float = 0.8


@dataclass(slots=True)
class ClassificationResult:
    category: str
    confidence: float
    reasoning: str


@dataclass(slots=True)
class ExtractionResult:
    key: str
    label: str
    value: str | None
    value_type: str
    value_numeric: Decimal | None
    page_number: int | None
    confidence: float
    bbox: tuple[float, float, float, float] | None
    extraction_method: str
    extraction_note: str | None = None
    sheet_name: str | None = None
    row_label: str | None = None
    column_header: str | None = None
    cell_reference: str | None = None
