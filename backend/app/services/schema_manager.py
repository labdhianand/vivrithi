from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..extraction_schemas import DEFAULT_SCHEMAS
from ..models.schema import ExtractionSchema


def get_default_schema(category: str) -> dict:
    if category not in DEFAULT_SCHEMAS:
        raise KeyError(f"Unsupported category: {category}")
    return DEFAULT_SCHEMAS[category]


async def get_case_schemas(session: AsyncSession, case_id: str) -> list[ExtractionSchema]:
    result = await session.execute(
        select(ExtractionSchema).where(ExtractionSchema.case_id == case_id).order_by(ExtractionSchema.document_category)
    )
    return list(result.scalars().all())


async def get_or_create_case_schema(session: AsyncSession, case_id: str, category: str) -> ExtractionSchema:
    result = await session.execute(
        select(ExtractionSchema)
        .where(ExtractionSchema.case_id == case_id, ExtractionSchema.document_category == category)
        .order_by(ExtractionSchema.schema_version.desc())
    )
    existing = result.scalars().first()
    if existing:
        return existing
    default = get_default_schema(category)
    schema = ExtractionSchema(
        case_id=case_id,
        document_category=category,
        schema_version=1,
        fields=default["fields"],
        is_default=True,
    )
    session.add(schema)
    await session.commit()
    await session.refresh(schema)
    return schema

