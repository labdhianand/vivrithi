from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..models.document import Document
from ..schemas.ops import FailedDocumentJobListRead, FailedDocumentJobRead


router = APIRouter()


@router.get("/ops/failed-jobs/documents", response_model=FailedDocumentJobListRead)
async def list_failed_document_jobs(
    session: AsyncSession = Depends(get_session),
) -> FailedDocumentJobListRead:
    result = await session.execute(
        select(Document, Case)
        .join(Case, Case.id == Document.case_id)
        .where(Document.processing_status == "failed")
        .order_by(Document.updated_at.desc())
    )
    items = [
        FailedDocumentJobRead(
            case_id=document.case_id,
            case_name=case.company_name,
            document_id=document.id,
            original_filename=document.original_filename,
            processing_status=document.processing_status,
            failure_reason=document.failure_reason,
            updated_at=document.updated_at,
            retry_available=True,
        )
        for document, case in result.all()
    ]
    return FailedDocumentJobListRead(total_failed_documents=len(items), items=items)
