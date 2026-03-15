from __future__ import annotations

import json
import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.case import Case, CrossVerification
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from ..models.score import Score
from .cross_verifier import cross_verify, llm_triangulate
from .five_cs_scorer import score_five_cs
from .ml_scorer import get_model_metadata, predict_default_probability
from .recommendation import generate_recommendation
from .research_agent import run_secondary_research
from .swot_generator import generate_swot

logger = logging.getLogger(__name__)


async def _get_documents(session: AsyncSession, case_id: str) -> list[Document]:
    result = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    return list(result.scalars().all())


async def _get_extractions(session: AsyncSession, case_id: str) -> list[Extraction]:
    result = await session.execute(
        select(Extraction)
        .join(Document, Document.id == Extraction.document_id)
        .where(Document.case_id == case_id)
        .options(selectinload(Extraction.document))
    )
    return list(result.scalars().all())


async def _get_research(session: AsyncSession, case_id: str) -> list[ResearchItem]:
    result = await session.execute(select(ResearchItem).where(ResearchItem.case_id == case_id))
    return list(result.scalars().all())


async def run_case_analysis(session: AsyncSession, case: Case, notes: list) -> Score:
    documents = await _get_documents(session, case.id)
    extractions = await _get_extractions(session, case.id)
    research_items = await _get_research(session, case.id)
    if not research_items:
        nse_symbol = next(
            (item.value for item in extractions if item.schema_field_key == "nse_symbol" and item.value),
            None,
        )
        for payload in await run_secondary_research(case, nse_symbol=nse_symbol, extractions=extractions):
            session.add(ResearchItem(case_id=case.id, **payload))
        await session.commit()
        research_items = await _get_research(session, case.id)

    cross_checks = cross_verify(case, documents, extractions)
    # LLM triangulation: additive checks, never removes existing ones
    try:
        llm_checks = llm_triangulate(case.id, extractions, research_items)
        cross_checks.extend(llm_checks)
    except Exception as exc:
        logger.warning(f"LLM triangulation failed for case {case.id}: {exc}")
    await session.execute(delete(CrossVerification).where(CrossVerification.case_id == case.id))
    for check in cross_checks:
        session.add(CrossVerification(**check))
    await session.commit()

    five_cs = score_five_cs(extractions, research_items, notes)

    # Build extraction map for ML scorer and SWOT
    extraction_map = {
        extraction.schema_field_key: extraction.user_edited_value or extraction.value
        for extraction in extractions
        if extraction.user_edited_value or extraction.value
    }

    # ML-based risk scoring
    ml_prediction = None
    try:
        ml_prediction = predict_default_probability(
            five_cs, extraction_map, research_items, case
        )
        logger.info(
            f"ML prediction for case {case.id}: PD={ml_prediction['pd_probability']:.4f}, "
            f"grade={ml_prediction['ml_grade']}, decision={ml_prediction['ml_decision']}"
        )
    except Exception as exc:
        logger.warning(f"ML scoring failed for case {case.id}: {exc}")

    # Attach model metadata to ML prediction for transparency
    if ml_prediction:
        try:
            ml_prediction["model_metadata"] = get_model_metadata()
        except Exception:
            pass

    recommendation = generate_recommendation(
        case, five_cs, cross_checks, research_items, ml_prediction=ml_prediction
    )
    swot = generate_swot(case, five_cs, research_items, extraction_map)

    existing_result = await session.execute(select(Score).where(Score.case_id == case.id))
    score = existing_result.scalars().first()
    if score is None:
        score = Score(case_id=case.id)
        session.add(score)

    score.character_score = five_cs["character"].score
    score.character_reasoning = five_cs["character"].reasoning
    score.capacity_score = five_cs["capacity"].score
    score.capacity_reasoning = five_cs["capacity"].reasoning
    score.capital_score = five_cs["capital"].score
    score.capital_reasoning = five_cs["capital"].reasoning
    score.collateral_score = five_cs["collateral"].score
    score.collateral_reasoning = five_cs["collateral"].reasoning
    score.conditions_score = five_cs["conditions"].score
    score.conditions_reasoning = five_cs["conditions"].reasoning
    score.overall_score = five_cs["overall_score"]
    score.risk_grade = five_cs["risk_grade"]
    score.recommendation = recommendation["recommendation"]
    score.recommended_amount_crore = recommendation["recommended_amount_crore"]
    score.recommended_rate_percent = recommendation["recommended_rate_percent"]
    score.recommended_tenure_months = recommendation["recommended_tenure_months"]
    score.decision_reasoning = recommendation["decision_reasoning"]
    score.key_strengths = recommendation["key_strengths"]
    score.key_risks = recommendation["key_risks"]
    score.conditions_precedent = recommendation["conditions_precedent"]
    score.conditions_subsequent = recommendation["conditions_subsequent"]
    score.monitoring_covenants = recommendation["monitoring_covenants"]
    score.improvement_scenarios = recommendation.get("improvement_scenarios") or []
    score.swot = swot
    case.status = "analyzing"

    await session.commit()
    await session.refresh(score)
    return score


def parse_reasoning_factors(reasoning: str | None) -> list[dict]:
    if not reasoning:
        return []
    try:
        return json.loads(reasoning).get("factors", [])
    except json.JSONDecodeError:
        return []
