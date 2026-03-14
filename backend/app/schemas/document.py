from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    original_filename: str
    stored_path: str
    file_size_bytes: int | None = None
    mime_type: str | None = None
    sha256_hash: str | None = None
    auto_category: str | None = None
    auto_category_confidence: Decimal | None = None
    user_category: str | None = None
    classification_status: str
    processing_status: str
    total_pages: int | None = None
    raw_markdown: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentClassificationUpdate(BaseModel):
    user_category: str
    classification_status: str = "user_approved"


class DocumentProcessRead(BaseModel):
    document: DocumentRead
    message: str


class DocumentPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_number: int
    is_scanned: bool | None = None
    has_tables: bool | None = None
    content_type: str | None = None
    parser_used: str | None = None
    raw_text: str | None = None
    raw_markdown: str | None = None
    page_image_path: str | None = None
    parsing_confidence: Decimal | None = None
    parsing_duration_ms: int | None = None
    created_at: datetime
    updated_at: datetime

