from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    report_type: str
    format: str
    stored_path: str | None = None
    sections: list[dict] | None = None
    created_at: datetime
    updated_at: datetime


class ReportPreviewRead(BaseModel):
    report: ReportRead
    sections: list[dict]

