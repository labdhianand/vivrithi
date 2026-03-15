from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..schemas.databricks import DatabricksCasePreviewRead, DatabricksStatusRead
from ..services.databricks import get_databricks_service


router = APIRouter()


@router.get("/integrations/databricks/status", response_model=DatabricksStatusRead)
async def get_databricks_status() -> DatabricksStatusRead:
    service = get_databricks_service()
    health = await service.healthcheck()
    return DatabricksStatusRead(
        configured=health.configured,
        reachable=health.reachable,
        host=service.settings.databricks_host,
        warehouse_id=service.settings.databricks_warehouse_id,
        detail=health.detail,
    )


@router.get("/cases/{case_id}/integrations/databricks/preview", response_model=DatabricksCasePreviewRead)
async def preview_case_databricks_queries(
    case_id: str,
    session: AsyncSession = Depends(get_session),
) -> DatabricksCasePreviewRead:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    service = get_databricks_service()
    return DatabricksCasePreviewRead(
        case_id=case_id,
        configured=service.is_configured(),
        query_templates=service.build_case_query_templates(case),
    )
