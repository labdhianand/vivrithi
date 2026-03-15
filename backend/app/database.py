from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


settings = get_settings()
engine = create_async_engine(settings.database_url, future=True, echo=False)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from .models import (  # noqa: F401
        analyst_note,
        case,
        document,
        extraction,
        page,
        report,
        research,
        schema,
        score,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _apply_runtime_migrations(conn)


async def _apply_runtime_migrations(conn) -> None:
    dialect = conn.engine.dialect.name
    if dialect != "sqlite":
        return
    await _ensure_sqlite_columns(
        conn,
        "research_items",
        {
            "entity_scope": "VARCHAR(32)",
            "entity_match_score": "NUMERIC(5, 4)",
            "verification_status": "VARCHAR(32)",
            "matched_terms": "TEXT",
            "match_explanation": "TEXT",
        },
    )
    await _ensure_sqlite_columns(
        conn,
        "documents",
        {
            "failure_reason": "TEXT",
        },
    )
    await _ensure_sqlite_columns(
        conn,
        "extractions",
        {
            "correction_type": "VARCHAR(64)",
            "sheet_name": "VARCHAR(255)",
            "row_label": "TEXT",
            "column_header": "TEXT",
            "cell_reference": "VARCHAR(32)",
        },
    )
    await _ensure_sqlite_columns(
        conn,
        "scores",
        {
            "improvement_scenarios": "JSON",
        },
    )


async def _ensure_sqlite_columns(conn, table_name: str, columns: dict[str, str]) -> None:
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    existing_columns = {row[1] for row in result.fetchall()}
    for column_name, column_type in columns.items():
        if column_name in existing_columns:
            continue
        await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
