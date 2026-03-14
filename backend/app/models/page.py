from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .base import TimestampMixin, UUIDPrimaryKeyMixin


class Page(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pages"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number: Mapped[int]
    is_scanned: Mapped[bool | None]
    has_tables: Mapped[bool | None]
    content_type: Mapped[str | None] = mapped_column(String(64))
    parser_used: Mapped[str | None] = mapped_column(String(64))
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_markdown: Mapped[str | None] = mapped_column(Text)
    page_image_path: Mapped[str | None] = mapped_column(Text)
    parsing_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    parsing_duration_ms: Mapped[int | None]

    document = relationship("Document", back_populates="pages")
