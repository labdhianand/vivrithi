from __future__ import annotations

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
        await process_document(session, case, document, backend=backend)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = await session.execute(
        select(Extraction).where(Extraction.document_id == doc_id).order_by(Extraction.schema_field_key)
    )
    return list(result.scalars().all())
