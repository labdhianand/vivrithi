from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models.case import Case
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.page import Page
from .runtime import FastDocumentPipeline, get_docling_remote_backend, parsed_pages_from_remote_payload
from .classifier import classify_document
from .extractor import extract_with_schema
from .markdown_builder import build_document_markdown
from .parser_landingai import parse_page_landingai
from .parser_pdfplumber import parse_page_pdfplumber
from .parser_router import route_page
from .parser_vision import parse_page_gemini_vision
from .pdf_triage import classify_page_content, triage_document
from .schema_manager import get_or_create_case_schema
from .storage import storage
from .types import ParsedPage


def _normalize_bbox(value: object) -> tuple[float | None, float | None, float | None, float | None]:
    if not isinstance(value, (list, tuple)):
        return (None, None, None, None)
    normalized = list(value[:4])
    while len(normalized) < 4:
        normalized.append(None)
    return tuple(normalized)


async def _reset_document_outputs(session: AsyncSession, document_id: str) -> None:
    await session.execute(delete(Page).where(Page.document_id == document_id))
    await session.execute(delete(Extraction).where(Extraction.document_id == document_id))
    await session.commit()


def _build_extraction_model(document: Document, page_model: Page | None, result) -> Extraction:
    bbox = _normalize_bbox(result.bbox)
    return Extraction(
        document_id=document.id,
        page_id=page_model.id if page_model else None,
        schema_field_key=result.key,
        field_label=result.label,
        value=result.value,
        value_type=result.value_type,
        value_numeric=result.value_numeric,
        source_page_number=result.page_number,
        bbox_x1=bbox[0],
        bbox_y1=bbox[1],
        bbox_x2=bbox[2],
        bbox_y2=bbox[3],
        confidence=Decimal(str(round(result.confidence, 4))),
        extraction_method=result.extraction_method,
        sheet_name=getattr(result, "sheet_name", None),
        row_label=getattr(result, "row_label", None),
        column_header=getattr(result, "column_header", None),
        cell_reference=getattr(result, "cell_reference", None),
    )


async def _process_document_legacy(session: AsyncSession, case: Case, document: Document) -> Document:
    document.processing_status = "triaging"
    document.failure_reason = None
    await session.commit()
    pdf_path = storage.absolute_path(document.stored_path)
    triage_results = triage_document(pdf_path, case.id, document.id)

    await _reset_document_outputs(session, document.id)

    parsed_pages: list[ParsedPage] = []
    page_models_by_number: dict[int, Page] = {}
    for triage in triage_results:
        parser_used = route_page(triage)
        if parser_used == "skip":
            parsed = ParsedPage(
                page_number=triage.page_number,
                text=triage.text_content,
                markdown=triage.text_content,
                parser_used="skip",
                confidence=1.0,
            )
        elif parser_used == "landingai":
            parsed = await parse_page_landingai(
                pdf_path=pdf_path,
                page_num=triage.page_number - 1,
                page_image_path=storage.absolute_path(triage.image_path),
            )
        elif parser_used == "gemini_vision":
            parsed = await parse_page_gemini_vision(
                pdf_path=pdf_path,
                page_num=triage.page_number - 1,
                page_image_path=storage.absolute_path(triage.image_path),
            )
        else:
            parsed = parse_page_pdfplumber(pdf_path, triage.page_number - 1)
        parsed_pages.append(parsed)

        page_model = Page(
            document_id=document.id,
            page_number=triage.page_number,
            is_scanned=triage.is_scanned,
            has_tables=triage.has_tables,
            content_type=triage.content_type,
            parser_used=parsed.parser_used,
            raw_text=parsed.text,
            raw_markdown=parsed.markdown,
            page_image_path=triage.image_path,
            parsing_confidence=Decimal(str(round(parsed.confidence, 4))),
            parsing_duration_ms=0,
        )
        session.add(page_model)
        await session.flush()
        page_models_by_number[triage.page_number] = page_model

    document.total_pages = len(triage_results)
    document.processing_status = "parsing"
    document.raw_markdown = build_document_markdown(parsed_pages)
    first_pages_markdown = "\n\n".join(page.markdown for page in parsed_pages[:3])
    page_signal_counts = Counter(triage.content_type for triage in triage_results)
    classification = await classify_document(
        first_pages_markdown,
        filename=document.original_filename,
        page_signal_counts=dict(page_signal_counts),
    )
    document.auto_category = classification.category
    document.auto_category_confidence = Decimal(str(round(classification.confidence, 4)))
    if not document.user_category:
        document.user_category = classification.category
    if document.classification_status == "pending":
        document.classification_status = "auto_classified"

    schema = await get_or_create_case_schema(session, case.id, document.user_category)
    document.processing_status = "extracting"
    await session.commit()

    extraction_results = await extract_with_schema(
        pdf_path=pdf_path,
        document_markdown=document.raw_markdown,
        schema={"category": schema.document_category, "fields": schema.fields},
        pages=parsed_pages,
    )
    for result in extraction_results:
        page_model = page_models_by_number.get(result.page_number or 0)
        session.add(_build_extraction_model(document, page_model, result))

    document.processing_status = "extracted"
    case.status = "extracted"
    await session.commit()
    await session.refresh(document)
    return document


async def _process_document_fast(session: AsyncSession, case: Case, document: Document) -> Document:
    settings = get_settings()
    document.processing_status = "parsing"
    document.failure_reason = None
    await session.commit()
    pdf_path = storage.absolute_path(document.stored_path)
    await _reset_document_outputs(session, document.id)

    pipeline = FastDocumentPipeline(max_workers=settings.document_processing_max_workers)
    result = await pipeline.run_with_options(
        pdf_path,
        extraction_category=document.user_category,
    )

    page_models_by_number: dict[int, Page] = {}
    for page in result.document.pages:
        page_model = Page(
            document_id=document.id,
            page_number=page.page_number,
            is_scanned=page.is_scanned,
            has_tables=page.has_tables,
            content_type=page.content_type,
            parser_used=page.route,
            raw_text=page.text,
            raw_markdown=page.markdown,
            page_image_path=None,
            parsing_confidence=Decimal(str(round(0.92 if page.has_text_layer else 0.65, 4))),
            parsing_duration_ms=int(round(page.parse_seconds * 1000)),
        )
        session.add(page_model)
        await session.flush()
        page_models_by_number[page.page_number] = page_model

    document.total_pages = result.document.page_count
    document.raw_markdown = result.document.markdown
    document.auto_category = result.classification_category
    document.auto_category_confidence = Decimal(str(round(result.classification_confidence, 4)))
    if not document.user_category:
        document.user_category = result.extraction.schema_category
    if document.classification_status == "pending":
        document.classification_status = "auto_classified"

    document.processing_status = "extracting"
    await session.commit()

    for extracted in result.extraction.extraction_results:
        page_model = page_models_by_number.get(extracted.page_number or 0)
        session.add(_build_extraction_model(document, page_model, extracted))

    document.processing_status = "extracted"
    case.status = "extracted"
    await session.commit()
    await session.refresh(document)
    return document


async def _process_document_docling_remote(session: AsyncSession, case: Case, document: Document) -> Document:
    document.processing_status = "parsing"
    document.failure_reason = None
    await session.commit()
    source_path = storage.absolute_path(document.stored_path)
    await _reset_document_outputs(session, document.id)

    remote_backend = get_docling_remote_backend()
    remote_result = await remote_backend.convert(source_path)
    parsed_pages = parsed_pages_from_remote_payload(remote_result.payload)

    page_models_by_number: dict[int, Page] = {}
    page_signal_counts: Counter[str] = Counter()
    page_duration_ms = int(
        round((remote_result.convert_seconds / max(len(parsed_pages), 1)) * 1000)
    )
    document.total_pages = len(parsed_pages)
    await session.commit()
    for parsed_page in parsed_pages:
        has_tables = bool(parsed_page.tables)
        is_scanned = False
        content_type = classify_page_content(parsed_page.text, is_scanned, has_tables)
        page_signal_counts[content_type] += 1
        page_model = Page(
            document_id=document.id,
            page_number=parsed_page.page_number,
            is_scanned=is_scanned,
            has_tables=has_tables,
            content_type=content_type,
            parser_used=parsed_page.parser_used or remote_result.payload.get("backend") or "docling_gpu_remote",
            raw_text=parsed_page.text,
            raw_markdown=parsed_page.markdown,
            page_image_path=None,
            parsing_confidence=Decimal("0.9400"),
            parsing_duration_ms=page_duration_ms,
        )
        session.add(page_model)
        await session.flush()
        page_models_by_number[parsed_page.page_number] = page_model

    document.raw_markdown = remote_result.markdown or build_document_markdown(parsed_pages)
    first_pages_markdown = "\n\n".join(page.markdown for page in parsed_pages[:3])
    document.processing_status = "classifying"
    await session.commit()
    classification = await classify_document(
        first_pages_markdown or document.raw_markdown or "",
        filename=document.original_filename,
        page_signal_counts=dict(page_signal_counts),
    )
    document.auto_category = classification.category
    document.auto_category_confidence = Decimal(str(round(classification.confidence, 4)))
    if not document.user_category:
        document.user_category = classification.category
    if document.classification_status == "pending":
        document.classification_status = "auto_classified"

    schema = await get_or_create_case_schema(session, case.id, document.user_category)
    document.processing_status = "extracting"
    await session.commit()

    extraction_results = await extract_with_schema(
        pdf_path=source_path,
        document_markdown=document.raw_markdown,
        schema={"category": schema.document_category, "fields": schema.fields},
        pages=parsed_pages,
    )
    for result in extraction_results:
        page_model = page_models_by_number.get(result.page_number or 0)
        session.add(_build_extraction_model(document, page_model, result))

    document.processing_status = "extracted"
    case.status = "extracted"
    await session.commit()
    await session.refresh(document)
    return document


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff"}


async def _process_document_image(session: AsyncSession, case: Case, document: Document) -> Document:
    """Process an uploaded image file through Gemini vision OCR, then classify and extract."""
    document.processing_status = "parsing"
    document.failure_reason = None
    await session.commit()
    source_path = storage.absolute_path(document.stored_path)
    await _reset_document_outputs(session, document.id)

    # Create a single Page record for the image
    page_image_relative = document.stored_path  # The image itself is the page image
    page_model = Page(
        document_id=document.id,
        page_number=1,
        is_scanned=True,
        has_tables=False,
        content_type="scanned",
        parser_used="gemini_vision",
        raw_text="",
        raw_markdown="",
        page_image_path=page_image_relative,
        parsing_confidence=Decimal("0.8000"),
        parsing_duration_ms=0,
    )
    session.add(page_model)
    await session.flush()

    # Run Gemini vision OCR on the image
    parsed = await parse_page_gemini_vision(
        pdf_path=source_path,
        page_num=0,
        page_image_path=source_path,
    )
    page_model.raw_text = parsed.text
    page_model.raw_markdown = parsed.markdown
    page_model.parsing_confidence = Decimal(str(round(parsed.confidence, 4)))

    document.total_pages = 1
    document.raw_markdown = parsed.markdown

    # Classify
    document.processing_status = "classifying"
    await session.commit()
    classification = await classify_document(
        parsed.markdown,
        filename=document.original_filename,
    )
    document.auto_category = classification.category
    document.auto_category_confidence = Decimal(str(round(classification.confidence, 4)))
    if not document.user_category:
        document.user_category = classification.category
    if document.classification_status == "pending":
        document.classification_status = "auto_classified"

    # Extract
    schema = await get_or_create_case_schema(session, case.id, document.user_category)
    document.processing_status = "extracting"
    await session.commit()

    parsed_pages = [ParsedPage(
        page_number=1,
        text=parsed.text,
        markdown=parsed.markdown,
        parser_used="gemini_vision",
        confidence=parsed.confidence,
    )]
    extraction_results = await extract_with_schema(
        pdf_path=source_path,
        document_markdown=document.raw_markdown,
        schema={"category": schema.document_category, "fields": schema.fields},
        pages=parsed_pages,
    )
    for result in extraction_results:
        session.add(_build_extraction_model(document, page_model, result))

    document.processing_status = "extracted"
    case.status = "extracted"
    await session.commit()
    await session.refresh(document)
    return document


async def process_document(
    session: AsyncSession,
    case: Case,
    document: Document,
    backend: str | None = None,
) -> Document:
    # Check if this is an image file — route to image pipeline
    suffix = Path(document.original_filename or "").suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return await _process_document_image(session, case, document)

    selected_backend = (backend or get_settings().document_processing_backend).strip().lower()
    if selected_backend in {"legacy", "classic"}:
        return await _process_document_legacy(session, case, document)
    if selected_backend in {"fast", "fast_runtime"}:
        return await _process_document_fast(session, case, document)
    if selected_backend in {
        "docling",
        "docling_remote",
        "docling_gpu",
        "docling_gpu_remote",
        "marker",
        "marker_api",
        "marker_remote",
    }:
        return await _process_document_docling_remote(session, case, document)
    raise ValueError(f"Unsupported document processing backend: {selected_backend}")
