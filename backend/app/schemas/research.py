from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ResearchItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    category: str
    title: str | None = None
    summary: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    published_date: date | None = None
    sentiment: str | None = None
    severity: str | None = None
    relevance_score: Decimal | None = None
    affected_c: str | None = None
    impact_description: str | None = None
    created_at: datetime
    updated_at: datetime

