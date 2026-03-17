from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..utils import clean_text
from .docling_adapter import DoclingBackend, DoclingResult
from .docling_remote import get_docling_remote_backend
from .pipeline import FastDocumentPipeline
from .types import FastPipelineResult, GeometryBox


@dataclass(slots=True)
class ArtifactBBox:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(slots=True)
class ArtifactPage:
    page_number: int
    width: float
    height: float
    has_text_layer: bool
    has_tables: bool
    is_scanned: bool
    route: str


@dataclass(slots=True)
class ArtifactTextBlock:
    block_id: str
    page_number: int
    label: str
    text: str
    bbox: ArtifactBBox | None
    reading_order_index: int
    source_engine: str


@dataclass(slots=True)
class ArtifactTableCell:
    row_index: int
    column_index: int
    text: str
    bbox: ArtifactBBox | None


@dataclass(slots=True)
class ArtifactTable:
    table_id: str
    page_number: int
    bbox: ArtifactBBox | None
    markdown: str
    row_count: int
    column_count: int
    cells: list[ArtifactTableCell] = field(default_factory=list)
    source_engine: str = "native_pdf"


@dataclass(slots=True)
class ArtifactChunk:
    chunk_id: str
    text: str
    page_numbers: list[int]
    block_ids: list[str]
    headings: list[str]
    source_engine: str


@dataclass(slots=True)
class DocumentArtifact:
    backend: str
    document_name: str
    source_path: str
    page_count: int
    parse_seconds: float
    markdown: str
    text: str
    pages: list[ArtifactPage]
    text_blocks: list[ArtifactTextBlock]
    tables: list[ArtifactTable]
    reading_order: list[str]
    chunks: list[ArtifactChunk]
    raw_exports: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bbox_from_geometry(box: GeometryBox | None) -> ArtifactBBox | None:
    if box is None:
        return None
    return ArtifactBBox(x1=box.x1, y1=box.y1, x2=box.x2, y2=box.y2)


def _simple_fast_chunks(result: FastPipelineResult, max_chars: int = 1400) -> list[ArtifactChunk]:
    """Build semantic chunks with tables as atomic units, interleaved at page boundaries."""
    # Index tables by page.
    tables_by_page: dict[int, list] = {}
    for page in result.document.pages:
        for table in page.tables:
            if table.markdown and table.markdown.strip():
                tables_by_page.setdefault(page.page_number, []).append(table)

    chunks: list[ArtifactChunk] = []
    chunk_index = 0
    buffer_lines: list[str] = []
    buffer_pages: list[int] = []
    buffer_block_ids: list[str] = []
    emitted_table_pages: set[int] = set()
    prev_page: int | None = None

    def _flush_text() -> None:
        nonlocal chunk_index, buffer_lines, buffer_pages, buffer_block_ids
        if not buffer_lines:
            return
        chunks.append(
            ArtifactChunk(
                chunk_id=f"chunk-{chunk_index}",
                text=clean_text("\n".join(buffer_lines)),
                page_numbers=sorted(set(buffer_pages)),
                block_ids=buffer_block_ids[:],
                headings=[],
                source_engine="fast_runtime",
            )
        )
        chunk_index += 1
        buffer_lines = []
        buffer_pages = []
        buffer_block_ids = []

    def _emit_tables_for_page(page_number: int) -> None:
        nonlocal chunk_index
        if page_number in emitted_table_pages:
            return
        emitted_table_pages.add(page_number)
        for table in tables_by_page.get(page_number, []):
            chunks.append(
                ArtifactChunk(
                    chunk_id=f"chunk-{chunk_index}",
                    text=table.markdown,
                    page_numbers=[page_number],
                    block_ids=[f"p{page_number}-table"],
                    headings=[],
                    source_engine="fast_runtime",
                )
            )
            chunk_index += 1

    blocks = result_blocks_from_fast(result)
    for block in blocks:
        if prev_page is not None and block.page_number != prev_page:
            if len(clean_text("\n".join(buffer_lines))) > 200:
                _flush_text()
            _emit_tables_for_page(prev_page)
        prev_page = block.page_number

        candidate_text = clean_text("\n".join(buffer_lines + [block.text]))
        if buffer_lines and len(candidate_text) > max_chars:
            _flush_text()
        buffer_lines.append(block.text)
        buffer_pages.append(block.page_number)
        buffer_block_ids.append(block.block_id)

    _flush_text()
    if prev_page is not None:
        _emit_tables_for_page(prev_page)

    # Emit tables from pages with no text blocks.
    for page_number in sorted(tables_by_page.keys()):
        _emit_tables_for_page(page_number)

    return chunks


def result_blocks_from_fast(result: FastPipelineResult) -> list[ArtifactTextBlock]:
    blocks: list[ArtifactTextBlock] = []
    reading_order = 0
    for page in result.document.pages:
        for line_index, line in enumerate(page.lines):
            text = clean_text(line.text)
            if not text:
                continue
            blocks.append(
                ArtifactTextBlock(
                    block_id=f"p{page.page_number}-line-{line_index}",
                    page_number=page.page_number,
                    label="line",
                    text=text,
                    bbox=_bbox_from_geometry(line.bbox),
                    reading_order_index=reading_order,
                    source_engine=page.route,
                )
            )
            reading_order += 1
    return blocks


def artifact_from_fast_result(result: FastPipelineResult) -> DocumentArtifact:
    pages = [
        ArtifactPage(
            page_number=page.page_number,
            width=page.width,
            height=page.height,
            has_text_layer=page.has_text_layer,
            has_tables=page.has_tables,
            is_scanned=page.is_scanned,
            route=page.route,
        )
        for page in result.document.pages
    ]
    text_blocks = result_blocks_from_fast(result)
    tables: list[ArtifactTable] = []
    for page in result.document.pages:
        for table_index, table in enumerate(page.tables):
            cells: list[ArtifactTableCell] = []
            for row_index, row in enumerate(table.rows):
                for column_index, value in enumerate(row):
                    if value in (None, ""):
                        continue
                    cells.append(
                        ArtifactTableCell(
                            row_index=row_index,
                            column_index=column_index,
                            text=str(value),
                            bbox=None,
                        )
                    )
            tables.append(
                ArtifactTable(
                    table_id=f"p{page.page_number}-table-{table_index}",
                    page_number=page.page_number,
                    bbox=_bbox_from_geometry(table.bbox),
                    markdown=table.markdown,
                    row_count=table.row_count,
                    column_count=table.column_count,
                    cells=cells,
                    source_engine=page.route,
                )
            )
    reading_order = [block.block_id for block in text_blocks]
    markdown = result.document.markdown
    text = "\n".join(page.text for page in result.document.pages)
    return DocumentArtifact(
        backend="fast_runtime",
        document_name=result.document.pdf_path.name,
        source_path=str(result.document.pdf_path),
        page_count=result.document.page_count,
        parse_seconds=round(result.document.parse_seconds + result.extraction.extraction_seconds, 6),
        markdown=markdown,
        text=text,
        pages=pages,
        text_blocks=text_blocks,
        tables=tables,
        reading_order=reading_order,
        chunks=_simple_fast_chunks(result),
        raw_exports={
            "route_counts": result.document.route_counts,
            "content_type_counts": result.document.content_type_counts,
            "classification": {
                "category": result.classification_category,
                "confidence": result.classification_confidence,
            },
            "candidate_pages": [page.page_number for page in result.extraction.candidate_pages],
            "field_values": result.active_values(),
        },
    )


def artifact_from_docling(pdf_path: Path, backend: DoclingBackend) -> DocumentArtifact:
    result: DoclingResult = backend.convert(pdf_path)
    payload = result.document if isinstance(result.document, dict) else {}
    payload.setdefault("document_name", pdf_path.name)
    payload.setdefault("source_path", str(pdf_path))
    payload.setdefault("page_count", result.page_count)
    payload.setdefault("convert_seconds", round(result.convert_seconds, 6))
    payload.setdefault("markdown", result.markdown)
    payload.setdefault("text", result.text)
    return artifact_from_remote_payload(payload)


async def build_fast_artifact(pdf_path: Path, category: str | None = None, max_workers: int = 8) -> DocumentArtifact:
    pipeline = FastDocumentPipeline(max_workers=max_workers)
    result = await pipeline.run_with_options(pdf_path, extraction_category=category)
    return artifact_from_fast_result(result)


def build_docling_artifact(pdf_path: Path) -> DocumentArtifact:
    backend = DoclingBackend()
    return artifact_from_docling(pdf_path, backend)


def artifact_from_remote_payload(payload: dict[str, Any]) -> DocumentArtifact:
    backend_name = str(payload.get("backend") or payload.get("method") or "pdfplumber")
    pages = [
        ArtifactPage(
            page_number=int(page["page_number"]),
            width=float(page.get("width") or 1.0),
            height=float(page.get("height") or 1.0),
            has_text_layer=bool(page.get("text")),
            has_tables=bool(page.get("tables")),
            is_scanned=False,
            route=str(page.get("route") or page.get("parser_used") or backend_name),
        )
        for page in payload.get("pages", [])
    ]
    text_blocks = [
        ArtifactTextBlock(
            block_id=str(block.get("block_id") or f"text-{index}"),
            page_number=int(block.get("page_number") or 0),
            label=str(block.get("label") or "text"),
            text=block.get("text") or "",
            bbox=ArtifactBBox(*block["bbox"]) if block.get("bbox") else None,
            reading_order_index=int(block.get("reading_order_index") or index),
            source_engine=str(block.get("source_engine") or backend_name),
        )
        for index, block in enumerate(payload.get("text_blocks", []))
    ]
    tables = []
    for table in payload.get("tables", []):
        cells = [
            ArtifactTableCell(
                row_index=int(cell.get("row_index") or 0),
                column_index=int(cell.get("column_index") or 0),
                text=cell.get("text") or "",
                bbox=ArtifactBBox(*cell["bbox"]) if cell.get("bbox") else None,
            )
            for cell in table.get("cells", [])
        ]
        tables.append(
            ArtifactTable(
                table_id=str(table.get("table_id") or f"table-{len(tables)}"),
                page_number=int(table.get("page_number") or 0),
                bbox=ArtifactBBox(*table["bbox"]) if table.get("bbox") else None,
                markdown=table.get("markdown") or "",
                row_count=int(table.get("row_count") or 0),
                column_count=int(table.get("column_count") or 0),
                cells=cells,
                source_engine=str(table.get("source_engine") or backend_name),
            )
        )
    return DocumentArtifact(
        backend=backend_name,
        document_name=payload.get("document_name") or "",
        source_path=payload.get("source_path") or "",
        page_count=int(payload.get("page_count") or 0),
        parse_seconds=float(payload.get("convert_seconds") or 0.0),
        markdown=payload.get("markdown") or "",
        text=payload.get("text") or "",
        pages=pages,
        text_blocks=text_blocks,
        tables=tables,
        reading_order=[block.block_id for block in sorted(text_blocks, key=lambda item: item.reading_order_index)],
        chunks=[
            ArtifactChunk(
                chunk_id=f"page-{page.page_number}",
                text=next(
                    (
                        item.get("markdown") or ""
                        for item in payload.get("pages", [])
                        if int(item["page_number"]) == page.page_number
                    ),
                    "",
                ),
                page_numbers=[page.page_number],
                block_ids=[block.block_id for block in text_blocks if block.page_number == page.page_number],
                headings=[],
                source_engine=backend_name,
            )
            for page in pages
        ],
        raw_exports={"remote_payload": payload},
    )


async def build_docling_remote_artifact(source_path: Path) -> DocumentArtifact:
    backend = get_docling_remote_backend()
    result = await backend.convert(source_path)
    return artifact_from_remote_payload(result.payload)
