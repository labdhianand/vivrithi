from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionSchema(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_schemas"

    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    document_category: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    fields: Mapped[list[dict]] = mapped_column(JSON, default=list)
    is_default: Mapped[bool] = mapped_column(default=False)

    case = relationship("Case", back_populates="schemas")
