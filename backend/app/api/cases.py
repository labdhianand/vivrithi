from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case
from ..schemas.case import CaseCreate, CaseRead, CaseUpdate


router = APIRouter()


@router.post("", response_model=CaseRead)
async def create_case(payload: CaseCreate, session: AsyncSession = Depends(get_session)) -> Case:
    case = Case(**payload.model_dump())
    session.add(case)
    await session.commit()
    await session.refresh(case)
    return case


@router.get("", response_model=list[CaseRead])
async def list_cases(session: AsyncSession = Depends(get_session)) -> list[Case]:
    result = await session.execute(select(Case).order_by(Case.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{case_id}", response_model=CaseRead)
async def get_case(case_id: str, session: AsyncSession = Depends(get_session)) -> Case:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(case_id: str, payload: CaseUpdate, session: AsyncSession = Depends(get_session)) -> Case:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(case, key, value)
    await session.commit()
    await session.refresh(case)
    return case

