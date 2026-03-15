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


class AnalystNoteInterpretRequest(BaseModel):
    note_type: str | None = None
    content: str


class AnalystNoteInterpretRead(BaseModel):
    affected_c: str
    sentiment: str
    risk_adjustment: int
    rationale: str
    signals: list[str]
