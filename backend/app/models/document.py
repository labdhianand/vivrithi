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
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    classification_status: Mapped[str] = mapped_column(String(32), default="pending")
    classification_reason: Mapped[str | None] = mapped_column(Text)
    classification_text: Mapped[str | None] = mapped_column(Text)

    processing_status: Mapped[str] = mapped_column(String(32), default="pending")
    extraction_status: Mapped[str] = mapped_column(String(32), default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text)
    total_pages: Mapped[int | None]
    extracted_text: Mapped[str | None] = mapped_column(Text)
    raw_markdown: Mapped[str | None] = mapped_column(Text)

    case = relationship("Case", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")

    @property
    def doc_id(self) -> str:
        return self.id

    @property
    def filename(self) -> str:
        return self.original_filename

    @property
    def doc_type(self) -> str | None:
        return self.user_category or self.auto_category

    @property
    def confidence(self) -> Decimal | None:
        return self.auto_category_confidence

    @property
    def reason(self) -> str | None:
        return self.classification_reason

    @property
    def extracted(self) -> bool:
        return self.extraction_status == "extracted"

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
            "classified": "classified",
            "processing": "processing",
            "extraction_failed": "partial",
        }
        if self.status == "failed":
            return "failed"
        if self.extraction_status == "extracted":
            return "completed"
        if self.extraction_status == "processing":
            return "processing"
        if self.extraction_status == "extraction_failed":
            return "partial"
        if self.status == "classified":
            return "classified"
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
            "classified": 35,
            "processing": 70,
            "extraction_failed": 100,
        }
        if self.status == "failed":
            return 100
        if self.extraction_status == "extracted":
            return 100
        if self.extraction_status == "processing":
            return 70
        if self.extraction_status == "extraction_failed":
            return 100
        if self.status == "classified":
            return 35
        return progress_map.get(self.processing_status, 0)
