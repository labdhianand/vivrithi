from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field


class ExtractionBBoxRead(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float


class DiscoveredFieldRead(BaseModel):
    field_name: str
    field_type: str
    value_found: str
    reason: str


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
    correction_type: str | None = None
    sheet_name: str | None = None
    row_label: str | None = None
    column_header: str | None = None
    cell_reference: str | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=ExtractionBBoxRead | None)
    @property
    def bbox(self) -> ExtractionBBoxRead | None:
        if (
            self.source_page_number is None
            or self.bbox_x1 is None
            or self.bbox_y1 is None
            or self.bbox_x2 is None
            or self.bbox_y2 is None
        ):
            return None
        return ExtractionBBoxRead(
            page=self.source_page_number,
            x=float(self.bbox_x1),
            y=float(self.bbox_y1),
            width=max(0.0, float(self.bbox_x2) - float(self.bbox_x1)),
            height=max(0.0, float(self.bbox_y2) - float(self.bbox_y1)),
        )


class ExtractionUpdate(BaseModel):
    value: str | None = None
    user_edited_value: str | None = None
    user_verified: bool = True
    correction_type: str | None = None
