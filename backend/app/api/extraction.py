from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.page import Page
from ..schemas.extraction import ExtractionRead, ExtractionUpdate
from ..services.document_pipeline import _build_extraction_model, parsed_pages_from_page_models
from ..services.extractor import extract_with_schema
from ..services.schema_manager import get_or_create_case_schema
from ..services.storage import storage
from ..services.types import ParsedPage


router = APIRouter()
logger = logging.getLogger(__name__)
PROCESS_DOCUMENT_TIMEOUT_SECONDS = 60.0


def _derive_correction_type(extraction: Extraction, payload: ExtractionUpdate) -> str | None:
    if payload.correction_type:
        return payload.correction_type
    edited_value = payload.user_edited_value
    if edited_value is not None:
        baseline = payload.value if payload.value is not None else extraction.value
        if edited_value == "":
            return "override_cleared"
        if baseline != edited_value:
            return "value_changed"
        return "verified_no_change"
    if payload.user_verified:
        return "verified_no_change"
    return extraction.correction_type


@router.get("/documents/{doc_id}/extractions", response_model=list[ExtractionRead])
async def list_document_extractions(doc_id: str, session: AsyncSession = Depends(get_session)) -> list[Extraction]:
    result = await session.execute(
        select(Extraction).where(Extraction.document_id == doc_id).order_by(Extraction.schema_field_key)
    )
    return list(result.scalars().all())


@router.patch("/extractions/{extraction_id}", response_model=ExtractionRead)
async def update_extraction(
    extraction_id: str,
    payload: ExtractionUpdate,
    session: AsyncSession = Depends(get_session),
) -> Extraction:
    extraction = await session.get(Extraction, extraction_id)
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    if payload.value is not None:
        extraction.value = payload.value
    if payload.user_edited_value is not None:
        extraction.user_edited_value = payload.user_edited_value
    extraction.user_verified = payload.user_verified
    extraction.correction_type = _derive_correction_type(extraction, payload)
    await session.commit()
    await session.refresh(extraction)
    return extraction


@router.post("/documents/{doc_id}/extract", response_model=list[ExtractionRead])
async def rerun_extraction(
    doc_id: str,
    backend: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[Extraction]:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    case = await session.get(Case, document.case_id)
    schema_category = document.user_category or document.auto_category
    if not schema_category:
        raise HTTPException(status_code=400, detail="Document must be classified before extraction can run")

    schema = await get_or_create_case_schema(session, case.id, schema_category)
    page_result = await session.execute(
        select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
    )
    page_models = list(page_result.scalars().all())
    page_model_map = {page.page_number: page for page in page_models}
    parsed_pages = parsed_pages_from_page_models(page_models)
    document_markdown = document.extracted_text or document.raw_markdown or document.classification_text or ""
    if not parsed_pages and document_markdown:
        parsed_pages = [
            ParsedPage(
                page_number=1,
                text=document.classification_text or document_markdown,
                markdown=document_markdown,
                parser_used="stored_text",
                confidence=0.6,
            )
        ]
    if not document_markdown.strip():
        raise HTTPException(
            status_code=400,
            detail="Document text is not available yet. Wait for background extraction or retry later.",
        )

    try:
        extraction_results = await asyncio.wait_for(
            extract_with_schema(
                pdf_path=storage.absolute_path(document.stored_path),
                document_markdown=document_markdown,
                schema={"category": schema.document_category, "fields": schema.fields},
                pages=parsed_pages,
            ),
            timeout=PROCESS_DOCUMENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        document.failure_reason = f"Processing timed out after {PROCESS_DOCUMENT_TIMEOUT_SECONDS:g} seconds"
        await session.commit()
        logger.error("Document %s timed out during extraction rerun", doc_id)
        raise HTTPException(status_code=504, detail=document.failure_reason) from exc
    except ValueError as exc:
        document.failure_reason = str(exc)[:1000] or "Extraction rerun failed"
        await session.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        document.failure_reason = str(exc)[:1000] or "Extraction rerun failed"
        await session.commit()
        logger.exception("Document %s failed during extraction rerun", doc_id)
        raise HTTPException(status_code=500, detail=document.failure_reason) from exc
    await session.execute(delete(Extraction).where(Extraction.document_id == doc_id))
    for result in extraction_results:
        session.add(_build_extraction_model(document, page_model_map.get(result.page_number or 0), result))
    document.failure_reason = None
    await session.commit()
    result = await session.execute(
        select(Extraction).where(Extraction.document_id == doc_id).order_by(Extraction.schema_field_key)
    )
    return list(result.scalars().all())
