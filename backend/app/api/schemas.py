from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.schema import ExtractionSchema
from ..schemas.schema import SchemaRead, SchemaUpsert
from ..services.schema_manager import get_case_schemas, get_default_schema


router = APIRouter()


@router.get("/schemas/defaults/{category}", response_model=SchemaUpsert)
async def get_default_schema_endpoint(category: str) -> SchemaUpsert:
    try:
        default = get_default_schema(category)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SchemaUpsert(
        document_category=default["category"],
        fields=default["fields"],
        schema_version=1,
        is_default=True,
    )


@router.get("/cases/{case_id}/schemas", response_model=list[SchemaRead])
async def list_case_schemas(case_id: str, session: AsyncSession = Depends(get_session)) -> list[ExtractionSchema]:
    return await get_case_schemas(session, case_id)


@router.post("/cases/{case_id}/schemas", response_model=SchemaRead)
async def upsert_case_schema(
    case_id: str,
    payload: SchemaUpsert,
    session: AsyncSession = Depends(get_session),
) -> ExtractionSchema:
    result = await session.execute(
        select(ExtractionSchema)
        .where(
            ExtractionSchema.case_id == case_id,
            ExtractionSchema.document_category == payload.document_category,
        )
        .order_by(ExtractionSchema.schema_version.desc())
    )
    schema = result.scalars().first()
    if schema is None:
        schema = ExtractionSchema(
            case_id=case_id,
            document_category=payload.document_category,
            schema_version=payload.schema_version,
            fields=[field.model_dump() for field in payload.fields],
            is_default=payload.is_default,
        )
        session.add(schema)
    else:
        schema.fields = [field.model_dump() for field in payload.fields]
        schema.schema_version = payload.schema_version
        schema.is_default = payload.is_default
    await session.commit()
    await session.refresh(schema)
    return schema


@router.put("/cases/{case_id}/schemas/{schema_id}", response_model=SchemaRead)
async def update_schema(
    case_id: str,
    schema_id: str,
    payload: SchemaUpsert,
    session: AsyncSession = Depends(get_session),
) -> ExtractionSchema:
    schema = await session.get(ExtractionSchema, schema_id)
    if not schema or schema.case_id != case_id:
        raise HTTPException(status_code=404, detail="Schema not found")
    schema.document_category = payload.document_category
    schema.fields = [field.model_dump() for field in payload.fields]
    schema.schema_version = payload.schema_version
    schema.is_default = payload.is_default
    await session.commit()
    await session.refresh(schema)
    return schema

