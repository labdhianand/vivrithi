from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BBoxRead(BaseModel):
    x1: Decimal | None = None
    y1: Decimal | None = None
    x2: Decimal | None = None
    y2: Decimal | None = None


class TimestampedRead(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime | None = None


class DateValue(BaseModel):
    value: date | None = None


class MessageRead(BaseModel):
    message: str


class PaginatedRead(BaseModel):
    total: int = Field(default=0)

