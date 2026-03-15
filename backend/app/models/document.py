from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None]
    mime_type: Mapped[str | None] = mapped_column(String(255))
    sha256_hash: Mapped[str | None] = mapped_column(String(64))

    auto_category: Mapped[str | None] = mapped_column(String(64))
    auto_category_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    user_category: Mapped[str | None] = mapped_column(String(64))
    classification_status: Mapped[str] = mapped_column(String(32), default="pending")

    processing_status: Mapped[str] = mapped_column(String(32), default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text)
    total_pages: Mapped[int | None]
    raw_markdown: Mapped[str | None] = mapped_column(Text)

    case = relationship("Case", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")

    @property
    def current_stage(self) -> str:
        stage_map = {
            "pending": "pending",
            "queued": "queued",
            "triaging": "triaging",
            "parsing": "parsing",
            "classifying": "classifying",
            "extracting": "extracting",
            "extracted": "completed",
            "completed": "completed",
            "failed": "failed",
        }
        return stage_map.get(self.processing_status, self.processing_status or "pending")

    @property
    def progress_percent(self) -> int:
        progress_map = {
            "pending": 0,
            "queued": 5,
            "triaging": 15,
            "parsing": 55,
            "classifying": 72,
            "extracting": 88,
            "extracted": 100,
            "completed": 100,
            "failed": 100,
        }
        return progress_map.get(self.processing_status, 0)
