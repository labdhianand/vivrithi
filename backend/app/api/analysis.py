from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.analyst_note import AnalystNote
from ..models.case import Case, CrossVerification
from ..models.score import Score
from ..schemas.analysis import CScoreRead, CrossCheckRead, FiveCsRead, RecommendationRead, SWOTRead
from ..services.analysis_pipeline import parse_reasoning_factors, run_case_analysis


router = APIRouter()


def _build_cscore(name: str, score: int | None, reasoning: str | None) -> CScoreRead:
    factors = parse_reasoning_factors(reasoning)
    summary = f"{name} score {score}/100" if score is not None else f"{name} score unavailable"
    if factors:
        summary = factors[0]["signal"]
    return CScoreRead(score=score or 0, summary=summary, factors=factors)


def _build_five_cs_payload(score: Score) -> FiveCsRead:
    return FiveCsRead(
        id=score.id,
        case_id=score.case_id,
        character=_build_cscore("Character", score.character_score, score.character_reasoning),
        capacity=_build_cscore("Capacity", score.capacity_score, score.capacity_reasoning),
        capital=_build_cscore("Capital", score.capital_score, score.capital_reasoning),
        collateral=_build_cscore("Collateral", score.collateral_score, score.collateral_reasoning),
        conditions=_build_cscore("Conditions", score.conditions_score, score.conditions_reasoning),
        overall_score=score.overall_score or 0,
        risk_grade=score.risk_grade or "NA",
    )


@router.post("/cases/{case_id}/analyze", response_model=RecommendationRead)
async def analyze_case(case_id: str, session: AsyncSession = Depends(get_session)) -> RecommendationRead:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    notes_result = await session.execute(
        select(AnalystNote).where(AnalystNote.case_id == case_id).order_by(AnalystNote.created_at.desc())
    )
    score = await run_case_analysis(session, case, list(notes_result.scalars().all()))
    return RecommendationRead(
        recommendation=score.recommendation or "reject",
        overall_score=score.overall_score or 0,
        risk_grade=score.risk_grade or "NA",
        recommended_amount_crore=score.recommended_amount_crore,
        recommended_rate_percent=score.recommended_rate_percent,
        recommended_tenure_months=score.recommended_tenure_months,
        decision_reasoning=score.decision_reasoning or "",
        key_strengths=score.key_strengths or [],
        key_risks=score.key_risks or [],
        conditions_precedent=score.conditions_precedent or [],
        conditions_subsequent=score.conditions_subsequent or [],
        monitoring_covenants=score.monitoring_covenants or [],
    )


@router.get("/cases/{case_id}/cross-verification", response_model=list[CrossCheckRead])
async def get_cross_verification(case_id: str, session: AsyncSession = Depends(get_session)) -> list[CrossVerification]:
    result = await session.execute(
        select(CrossVerification).where(CrossVerification.case_id == case_id).order_by(CrossVerification.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/cases/{case_id}/five-cs", response_model=FiveCsRead)
async def get_five_cs(case_id: str, session: AsyncSession = Depends(get_session)) -> FiveCsRead:
    result = await session.execute(select(Score).where(Score.case_id == case_id))
    score = result.scalars().first()
    if not score:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _build_five_cs_payload(score)


@router.get("/cases/{case_id}/recommendation", response_model=RecommendationRead)
async def get_recommendation(case_id: str, session: AsyncSession = Depends(get_session)) -> RecommendationRead:
    result = await session.execute(select(Score).where(Score.case_id == case_id))
    score = result.scalars().first()
    if not score:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return RecommendationRead(
        recommendation=score.recommendation or "reject",
        overall_score=score.overall_score or 0,
        risk_grade=score.risk_grade or "NA",
        recommended_amount_crore=score.recommended_amount_crore,
        recommended_rate_percent=score.recommended_rate_percent,
        recommended_tenure_months=score.recommended_tenure_months,
        decision_reasoning=score.decision_reasoning or "",
        key_strengths=score.key_strengths or [],
        key_risks=score.key_risks or [],
        conditions_precedent=score.conditions_precedent or [],
        conditions_subsequent=score.conditions_subsequent or [],
        monitoring_covenants=score.monitoring_covenants or [],
    )


@router.get("/cases/{case_id}/swot", response_model=SWOTRead)
async def get_swot(case_id: str, session: AsyncSession = Depends(get_session)) -> SWOTRead:
    result = await session.execute(select(Score).where(Score.case_id == case_id))
    score = result.scalars().first()
    if not score or not score.swot:
        raise HTTPException(status_code=404, detail="SWOT not found")
    return SWOTRead(**score.swot)

