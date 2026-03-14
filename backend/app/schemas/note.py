from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalystNoteCreate(BaseModel):
    note_type: str | None = None
    content: str
    affected_c: str | None = None
    sentiment: str | None = None
    risk_adjustment: int | None = None


class AnalystNoteRead(AnalystNoteCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    created_at: datetime
    updated_at: datetime

