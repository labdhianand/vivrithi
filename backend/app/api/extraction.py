from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..models.document import Document
from ..models.extraction import Extraction
from ..schemas.extraction import ExtractionRead, ExtractionUpdate
from ..services.document_pipeline import process_document


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
    try:
        await asyncio.wait_for(
            process_document(session, case, document, backend=backend),
            timeout=PROCESS_DOCUMENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        document.processing_status = "failed"
        document.failure_reason = f"Processing timed out after {PROCESS_DOCUMENT_TIMEOUT_SECONDS:g} seconds"
        await session.commit()
        logger.error("Document %s timed out during extraction rerun", doc_id)
        raise HTTPException(status_code=504, detail=document.failure_reason) from exc
    except ValueError as exc:
        document.processing_status = "failed"
        document.failure_reason = str(exc)[:1000] or "Extraction rerun failed"
        await session.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        document.processing_status = "failed"
        document.failure_reason = str(exc)[:1000] or "Extraction rerun failed"
        await session.commit()
        logger.exception("Document %s failed during extraction rerun", doc_id)
        raise HTTPException(status_code=500, detail=document.failure_reason) from exc
    result = await session.execute(
        select(Extraction).where(Extraction.document_id == doc_id).order_by(Extraction.schema_field_key)
    )
    return list(result.scalars().all())
