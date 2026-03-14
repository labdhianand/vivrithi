from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SchemaField(BaseModel):
    key: str
    label: str
    type: str
    required: bool = False
    description: str | None = None


class SchemaUpsert(BaseModel):
    document_category: str
    fields: list[SchemaField]
    schema_version: int = 1
    is_default: bool = False


class SchemaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str | None = None
    document_category: str
    schema_version: int
    fields: list[SchemaField]
    is_default: bool
    created_at: datetime
    updated_at: datetime

