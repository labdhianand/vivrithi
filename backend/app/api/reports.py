from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.case import Case, CrossVerification
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.report import Report
from ..models.research import ResearchItem
from ..models.score import Score
from ..schemas.report import ReportPreviewRead, ReportRead
from ..services.analysis_pipeline import parse_reasoning_factors
from ..services.cam_generator import generate_cam_sections
from ..services.exporter import export_cam_docx, export_cam_pdf
from ..services.five_cs_scorer import CScore
from ..services.storage import storage


router = APIRouter()


def _rebuild_five_cs(score: Score) -> dict:
    return {
        "character": CScore("Character", score.character_score or 0, score.character_reasoning or "", "Character"),
        "capacity": CScore("Capacity", score.capacity_score or 0, score.capacity_reasoning or "", "Capacity"),
        "capital": CScore("Capital", score.capital_score or 0, score.capital_reasoning or "", "Capital"),
        "collateral": CScore("Collateral", score.collateral_score or 0, score.collateral_reasoning or "", "Collateral"),
        "conditions": CScore("Conditions", score.conditions_score or 0, score.conditions_reasoning or "", "Conditions"),
        "overall_score": score.overall_score or 0,
        "risk_grade": score.risk_grade or "NA",
    }


@router.post("/cases/{case_id}/reports/generate", response_model=ReportRead)
async def generate_report(case_id: str, session: AsyncSession = Depends(get_session)) -> Report:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    score_result = await session.execute(select(Score).where(Score.case_id == case_id))
    score = score_result.scalars().first()
    if not score:
        raise HTTPException(status_code=400, detail="Run analysis before generating report")

    documents = list((await session.execute(select(Document).where(Document.case_id == case_id))).scalars().all())
    extractions = list(
        (
            await session.execute(
                select(Extraction).join(Document, Document.id == Extraction.document_id).where(Document.case_id == case_id)
            )
        ).scalars().all()
    )
    research = list((await session.execute(select(ResearchItem).where(ResearchItem.case_id == case_id))).scalars().all())
    cross_checks = list(
        (await session.execute(select(CrossVerification).where(CrossVerification.case_id == case_id))).scalars().all()
    )
    cross_payload = [
        {
            "check_name": item.check_name,
            "status": item.status,
            "note": item.note,
            "value_a": item.value_a,
            "value_b": item.value_b,
        }
        for item in cross_checks
    ]
    recommendation = {
        "recommendation": score.recommendation or "reject",
        "risk_grade": score.risk_grade or "NA",
        "recommended_amount_crore": score.recommended_amount_crore,
        "recommended_rate_percent": score.recommended_rate_percent,
        "recommended_tenure_months": score.recommended_tenure_months,
        "decision_reasoning": score.decision_reasoning or "",
        "key_risks": score.key_risks or [],
    }
    five_cs = _rebuild_five_cs(score)
    for c_name in ["character", "capacity", "capital", "collateral", "conditions"]:
        factors = parse_reasoning_factors(getattr(score, f"{c_name}_reasoning"))
        five_cs[c_name].summary = factors[0]["signal"] if factors else f"{c_name.title()} score {getattr(score, f'{c_name}_score') or 0}"

    sections = generate_cam_sections(
        case=case,
        documents=documents,
        extractions=extractions,
        research=research,
        cross_checks=cross_payload,
        five_cs=five_cs,
        recommendation=recommendation | {"key_strengths": score.key_strengths or [], "conditions_precedent": score.conditions_precedent or [], "conditions_subsequent": score.conditions_subsequent or [], "monitoring_covenants": score.monitoring_covenants or []},
        swot=score.swot or {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
    )

    report = Report(case_id=case_id, report_type="cam", format="docx", sections=sections)
    session.add(report)
    await session.commit()
    await session.refresh(report)

    docx_bytes = export_cam_docx(case.company_name, sections)
    pdf_bytes = export_cam_pdf(case.company_name, sections)
    report.stored_path = storage.save_report_file(case_id, report.id, "docx", docx_bytes)
    storage.save_report_file(case_id, report.id, "pdf", pdf_bytes)
    case.status = "report_ready"
    await session.commit()
    await session.refresh(report)
    return report


@router.get("/cases/{case_id}/reports", response_model=list[ReportRead])
async def list_reports(case_id: str, session: AsyncSession = Depends(get_session)) -> list[Report]:
    result = await session.execute(select(Report).where(Report.case_id == case_id).order_by(Report.created_at.desc()))
    return list(result.scalars().all())


@router.get("/reports/{report_id}/preview", response_model=ReportPreviewRead)
async def preview_report(report_id: str, session: AsyncSession = Depends(get_session)) -> ReportPreviewRead:
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportPreviewRead(report=report, sections=report.sections or [])


@router.get("/reports/{report_id}/download/{format}")
async def download_report(report_id: str, format: str, session: AsyncSession = Depends(get_session)) -> FileResponse:
    if format not in {"docx", "pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported format")
    report = await session.get(Report, report_id)
    if not report or not report.stored_path:
        raise HTTPException(status_code=404, detail="Report not found")
    relative_path = report.stored_path.replace(".docx", f".{format}")
    absolute_path = storage.absolute_path(relative_path)
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(absolute_path, filename=f"{report_id}.{format}")

