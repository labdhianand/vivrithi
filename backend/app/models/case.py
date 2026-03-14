from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    cin: Mapped[str | None] = mapped_column(String(32))
    pan: Mapped[str | None] = mapped_column(String(16))
    sector: Mapped[str | None] = mapped_column(String(128))
    subsector: Mapped[str | None] = mapped_column(String(128))
    turnover_crore: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    incorporation_date: Mapped[date | None] = mapped_column(Date)
    registered_office: Mapped[str | None] = mapped_column(Text)

    loan_type: Mapped[str | None] = mapped_column(String(64))
    loan_amount_crore: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    loan_tenure_months: Mapped[int | None]
    proposed_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    loan_purpose: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="onboarding")

    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    schemas = relationship("ExtractionSchema", back_populates="case", cascade="all, delete-orphan")
    research_items = relationship("ResearchItem", back_populates="case", cascade="all, delete-orphan")
    analyst_notes = relationship("AnalystNote", back_populates="case", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="case", cascade="all, delete-orphan")


class CrossVerification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cross_verifications"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    check_name: Mapped[str] = mapped_column(String(128), nullable=False)
    doc_a: Mapped[str | None] = mapped_column(String(128))
    doc_b: Mapped[str | None] = mapped_column(String(128))
    value_a: Mapped[str | None] = mapped_column(Text)
    value_b: Mapped[str | None] = mapped_column(Text)
    discrepancy: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    note: Mapped[str | None] = mapped_column(Text)

    case = relationship("Case")
