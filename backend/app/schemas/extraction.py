from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_id: str | None = None
    schema_field_key: str
    field_label: str | None = None
    value: str | None = None
    value_type: str | None = None
    value_numeric: Decimal | None = None
    source_page_number: int | None = None
    bbox_x1: Decimal | None = None
    bbox_y1: Decimal | None = None
    bbox_x2: Decimal | None = None
    bbox_y2: Decimal | None = None
    confidence: Decimal | None = None
    extraction_method: str | None = None
    user_verified: bool = False
    user_edited_value: str | None = None
    created_at: datetime
    updated_at: datetime


class ExtractionUpdate(BaseModel):
    value: str | None = None
    user_edited_value: str | None = None
    user_verified: bool = True

