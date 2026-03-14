from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class AnalystNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyst_notes"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    note_type: Mapped[str | None] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    affected_c: Mapped[str | None] = mapped_column(String(64))
    sentiment: Mapped[str | None] = mapped_column(String(32))
    risk_adjustment: Mapped[int | None] = mapped_column(Integer)

    case = relationship("Case", back_populates="analyst_notes")
