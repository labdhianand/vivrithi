from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FailedDocumentJobRead(BaseModel):
    case_id: str
    case_name: str
    document_id: str
    original_filename: str
    processing_status: str
    failure_reason: str | None = None
    updated_at: datetime
    retry_available: bool = True


class FailedDocumentJobListRead(BaseModel):
    total_failed_documents: int
    items: list[FailedDocumentJobRead]
