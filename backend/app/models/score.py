from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Score(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scores"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    character_score: Mapped[int | None] = mapped_column(Integer)
    character_reasoning: Mapped[str | None] = mapped_column(Text)
    capacity_score: Mapped[int | None] = mapped_column(Integer)
    capacity_reasoning: Mapped[str | None] = mapped_column(Text)
    capital_score: Mapped[int | None] = mapped_column(Integer)
    capital_reasoning: Mapped[str | None] = mapped_column(Text)
    collateral_score: Mapped[int | None] = mapped_column(Integer)
    collateral_reasoning: Mapped[str | None] = mapped_column(Text)
    conditions_score: Mapped[int | None] = mapped_column(Integer)
    conditions_reasoning: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[int | None] = mapped_column(Integer)
    risk_grade: Mapped[str | None] = mapped_column(String(8))
    recommendation: Mapped[str | None] = mapped_column(String(64))
    recommended_amount_crore: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    recommended_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    recommended_tenure_months: Mapped[int | None] = mapped_column(Integer)
    decision_reasoning: Mapped[str | None] = mapped_column(Text)
    key_strengths: Mapped[list[dict] | None] = mapped_column(JSON)
    key_risks: Mapped[list[dict] | None] = mapped_column(JSON)
    conditions_precedent: Mapped[list[str] | None] = mapped_column(JSON)
    conditions_subsequent: Mapped[list[str] | None] = mapped_column(JSON)
    monitoring_covenants: Mapped[list[str] | None] = mapped_column(JSON)
    swot: Mapped[dict | None] = mapped_column(JSON)

    case = relationship("Case", back_populates="scores")
