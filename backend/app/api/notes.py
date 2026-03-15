from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.analyst_note import AnalystNote
from ..models.case import Case
from ..schemas.note import AnalystNoteCreate, AnalystNoteInterpretRead, AnalystNoteInterpretRequest, AnalystNoteRead
from ..services.note_interpreter import interpret_note, interpret_note_llm


router = APIRouter()


@router.post("/cases/{case_id}/notes", response_model=AnalystNoteRead)
async def create_note(
    case_id: str,
    payload: AnalystNoteCreate,
    session: AsyncSession = Depends(get_session),
) -> AnalystNote:
    case = await session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    note = AnalystNote(case_id=case_id, **payload.model_dump())
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.post("/cases/{case_id}/notes/interpret", response_model=AnalystNoteInterpretRead)
async def interpret_case_note(
    case_id: str,
    payload: AnalystNoteInterpretRequest,
    session: AsyncSession = Depends(get_session),
) -> AnalystNoteInterpretRead:
    case = await session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    llm_result = interpret_note_llm(payload.content, payload.note_type)
    result = llm_result if llm_result else interpret_note(payload.content, payload.note_type)
    return AnalystNoteInterpretRead(**result)


@router.get("/cases/{case_id}/notes", response_model=list[AnalystNoteRead])
async def list_notes(case_id: str, session: AsyncSession = Depends(get_session)) -> list[AnalystNote]:
    result = await session.execute(
        select(AnalystNote).where(AnalystNote.case_id == case_id).order_by(AnalystNote.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    note = await session.get(AnalystNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await session.delete(note)
    await session.commit()
    return {"message": "Note deleted"}
