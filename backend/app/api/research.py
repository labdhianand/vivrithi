from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from ..schemas.research import ResearchItemRead
from ..services.research_agent import run_secondary_research


router = APIRouter()


@router.post("/cases/{case_id}/research/run", response_model=list[ResearchItemRead])
async def run_research(case_id: str, session: AsyncSession = Depends(get_session)) -> list[ResearchItem]:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    extractions_result = await session.execute(
        select(Extraction).join(Document, Document.id == Extraction.document_id).where(Document.case_id == case_id)
    )
    extractions = list(extractions_result.scalars().all())
    extraction_result = await session.execute(
        select(Extraction.value)
        .join(Document, Document.id == Extraction.document_id)
        .where(Document.case_id == case_id, Extraction.schema_field_key == "nse_symbol")
    )
    nse_symbol = extraction_result.scalars().first()
    await session.execute(delete(ResearchItem).where(ResearchItem.case_id == case_id))
    for payload in await run_secondary_research(case, nse_symbol=nse_symbol, extractions=extractions):
        session.add(ResearchItem(case_id=case_id, **payload))
    await session.commit()
    result = await session.execute(
        select(ResearchItem).where(ResearchItem.case_id == case_id).order_by(ResearchItem.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/cases/{case_id}/research", response_model=list[ResearchItemRead])
async def list_research(case_id: str, session: AsyncSession = Depends(get_session)) -> list[ResearchItem]:
    result = await session.execute(
        select(ResearchItem).where(ResearchItem.case_id == case_id).order_by(ResearchItem.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/research/{item_id}")
async def delete_research_item(item_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    item = await session.get(ResearchItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Research item not found")
    await session.delete(item)
    await session.commit()
    return {"message": "Research item deleted"}
