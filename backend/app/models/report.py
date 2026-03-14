from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), default="cam")
    format: Mapped[str] = mapped_column(String(16), default="docx")
    stored_path: Mapped[str | None] = mapped_column(Text)
    sections: Mapped[list[dict] | None] = mapped_column(JSON)

    case = relationship("Case", back_populates="reports")
