from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Extraction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extractions"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_id: Mapped[str | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    schema_field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    field_label: Mapped[str | None] = mapped_column(String(255))
    value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str | None] = mapped_column(String(64))
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))

    source_page_number: Mapped[int | None]
    bbox_x1: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    bbox_y1: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    bbox_x2: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    bbox_y2: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))

    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    extraction_method: Mapped[str | None] = mapped_column(String(64))
    user_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user_edited_value: Mapped[str | None] = mapped_column(Text)

    document = relationship("Document", back_populates="extractions")
    page = relationship("Page")
