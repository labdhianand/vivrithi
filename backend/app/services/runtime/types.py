from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ..types import ExtractionResult, ParsedPage


@dataclass(slots=True)
class GeometryBox:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(slots=True)
class TokenGeometry:
    text: str
    bbox: GeometryBox
    confidence: float = 1.0
    source_engine: str = "native_pdf"


@dataclass(slots=True)
class LineGeometry:
    text: str
    bbox: GeometryBox
    token_indices: list[int] = field(default_factory=list)
    source_engine: str = "native_pdf"


@dataclass(slots=True)
class TableGeometry:
    bbox: GeometryBox
    markdown: str
    row_count: int
    column_count: int
    rows: list[list[str | None]] = field(default_factory=list)
    source_engine: str = "native_pdf"


@dataclass(slots=True)
class FastPageParse:
    page_number: int
    width: float
    height: float
    text: str
    markdown: str
    tokens: list[TokenGeometry] = field(default_factory=list)
    lines: list[LineGeometry] = field(default_factory=list)
    tables: list[TableGeometry] = field(default_factory=list)
    has_text_layer: bool = True
    has_tables: bool = False
    is_scanned: bool = False
    content_type: str = "narrative"
    route: str = "native_pdf"
    parse_seconds: float = 0.0

    def to_parsed_page(self) -> ParsedPage:
        from ..types import ParsedTable

        return ParsedPage(
            page_number=self.page_number,
            text=self.text,
            markdown=self.markdown,
            tables=[
                ParsedTable(
                    bbox=(table.bbox.x1, table.bbox.y1, table.bbox.x2, table.bbox.y2),
                    rows=table.rows,
                    markdown=table.markdown,
                )
                for table in self.tables
            ],
            bounding_boxes=[
                {
                    "text": token.text,
                    "bbox": (token.bbox.x1, token.bbox.y1, token.bbox.x2, token.bbox.y2),
                }
                for token in self.tokens
            ],
            parser_used=self.route,
            confidence=0.92 if self.has_text_layer else 0.65,
        )


@dataclass(slots=True)
class FastDocumentParse:
    pdf_path: Path
    pages: list[FastPageParse]
    markdown: str
    parse_seconds: float
    page_count: int
    route_counts: dict[str, int]
    content_type_counts: dict[str, int]


@dataclass(slots=True)
class CandidateSelection:
    field_key: str
    page_numbers: list[int]
    scores: dict[int, float]


@dataclass(slots=True)
class FieldResolutionTrace:
    field_key: str
    selected_pages: list[int]
    attempts: list[str]
    resolved: bool
    final_method: str


@dataclass(slots=True)
class FastExtractionArtifact:
    schema_category: str
    extraction_results: list[ExtractionResult]
    candidate_pages: list[FastPageParse]
    candidate_map: dict[str, CandidateSelection]
    resolution_traces: list[FieldResolutionTrace]
    extraction_seconds: float
    field_fill_count: int


@dataclass(slots=True)
class FastPipelineResult:
    document: FastDocumentParse
    classification_category: str
    classification_confidence: float
    extraction: FastExtractionArtifact

    def active_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for item in self.extraction.extraction_results:
            if item.value not in (None, "", "[]"):
                values[item.key] = item.value
        return values

    def numeric_values(self) -> dict[str, Decimal]:
        values: dict[str, Decimal] = {}
        for item in self.extraction.extraction_results:
            if item.value_numeric is not None:
                values[item.key] = item.value_numeric
        return values
