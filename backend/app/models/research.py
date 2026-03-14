from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class ResearchItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_items"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_name: Mapped[str | None] = mapped_column(String(255))
    published_date: Mapped[date | None] = mapped_column(Date)
    sentiment: Mapped[str | None] = mapped_column(String(32))
    severity: Mapped[str | None] = mapped_column(String(32))
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    affected_c: Mapped[str | None] = mapped_column(String(64))
    impact_description: Mapped[str | None] = mapped_column(Text)

    case = relationship("Case", back_populates="research_items")
