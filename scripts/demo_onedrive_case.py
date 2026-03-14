from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from shutil import copy2

from sqlalchemy import select

from backend.app.database import SessionLocal, init_db
from backend.app.models.case import Case, CrossVerification
from backend.app.models.document import Document
from backend.app.models.extraction import Extraction
from backend.app.models.report import Report
from backend.app.models.research import ResearchItem
from backend.app.services.analysis_pipeline import parse_reasoning_factors, run_case_analysis
from backend.app.services.cam_generator import generate_cam_sections
from backend.app.services.document_pipeline import process_document
from backend.app.services.exporter import export_cam_docx, export_cam_pdf
from backend.app.services.five_cs_scorer import CScore
from backend.app.services.storage import slugify, storage


ROOT = Path(__file__).resolve().parents[1]
ONEDRIVE = ROOT / "OneDrive_1_14-3-2026"
SAMPLE_DOCUMENTS = [
    ("ALM", ONEDRIVE / "ALM" / "file 01.xlsx"),
    ("Borrowing_Profile", ONEDRIVE / "BP" / "file 01.xlsx"),
    ("Portfolio_Performance", ONEDRIVE / "PC" / "file 01.xlsx"),
    ("Shareholding_Pattern", ONEDRIVE / "SHP" / "file 01.pdf"),
    ("Annual_Report", ONEDRIVE / "annual" / "1756892129-2.pdf"),
]


@dataclass(slots=True)
class ProcessSummary:
    document_id: str
    original_filename: str
    expected_category: str
    auto_category: str | None
    user_category: str | None
    total_pages: int | None
    processing_status: str
    elapsed_seconds: float


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def rebuild_five_cs(score) -> dict:
    payload = {
        "character": CScore("Character", score.character_score or 0, score.character_reasoning or "", "Character"),
        "capacity": CScore("Capacity", score.capacity_score or 0, score.capacity_reasoning or "", "Capacity"),
        "capital": CScore("Capital", score.capital_score or 0, score.capital_reasoning or "", "Capital"),
        "collateral": CScore("Collateral", score.collateral_score or 0, score.collateral_reasoning or "", "Collateral"),
        "conditions": CScore("Conditions", score.conditions_score or 0, score.conditions_reasoning or "", "Conditions"),
        "overall_score": score.overall_score or 0,
        "risk_grade": score.risk_grade or "NA",
    }
    for c_name in ["character", "capacity", "capital", "collateral", "conditions"]:
        factors = parse_reasoning_factors(getattr(score, f"{c_name}_reasoning"))
        payload[c_name].summary = (
            factors[0]["signal"]
            if factors
            else f"{c_name.title()} score {getattr(score, f'{c_name}_score') or 0}"
        )
    return payload


async def create_case() -> Case:
    async with SessionLocal() as session:
        case = Case(
            company_name="OneDrive Demo Borrower",
            cin="U65990MH2015PTC000001",
            sector="Financial Services",
            subsector="NBFC",
            loan_type="Term Loan",
            loan_amount_crore=Decimal("150.00"),
            loan_tenure_months=24,
            proposed_rate_percent=Decimal("11.50"),
            loan_purpose="Working capital and on-lending",
            status="onboarding",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case


async def stage_document(case_id: str, source_path: Path) -> Document:
    mime_type = "application/pdf" if source_path.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    async with SessionLocal() as session:
        document = Document(
            case_id=case_id,
            original_filename=source_path.name,
            stored_path="pending",
            file_size_bytes=source_path.stat().st_size,
            mime_type=mime_type,
            sha256_hash=sha256_bytes(source_path.read_bytes()),
            classification_status="pending",
            processing_status="pending",
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

        relative_path = f"cases/{case_id}/documents/{document.id}/{slugify(source_path.name)}"
        absolute_path = storage.absolute_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, absolute_path)
        document.stored_path = relative_path
        await session.commit()
        await session.refresh(document)
        return document


async def process_document_job(case_id: str, document_id: str, expected_category: str, backend: str) -> ProcessSummary:
    started = time.perf_counter()
    async with SessionLocal() as session:
        case = await session.get(Case, case_id)
        document = await session.get(Document, document_id)
        if case is None or document is None:
            raise RuntimeError(f"Missing case/document for {case_id}/{document_id}")
        processed = await process_document(session, case, document, backend=backend)
        return ProcessSummary(
            document_id=processed.id,
            original_filename=processed.original_filename,
            expected_category=expected_category,
            auto_category=processed.auto_category,
            user_category=processed.user_category,
            total_pages=processed.total_pages,
            processing_status=processed.processing_status,
            elapsed_seconds=round(time.perf_counter() - started, 3),
        )


async def generate_report(case_id: str, score) -> tuple[Report, Path, Path]:
    async with SessionLocal() as session:
        case = await session.get(Case, case_id)
        if case is None:
            raise RuntimeError(f"Case not found: {case_id}")
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
            "key_strengths": score.key_strengths or [],
            "key_risks": score.key_risks or [],
            "conditions_precedent": score.conditions_precedent or [],
            "conditions_subsequent": score.conditions_subsequent or [],
            "monitoring_covenants": score.monitoring_covenants or [],
        }
        sections = generate_cam_sections(
            case=case,
            documents=documents,
            extractions=extractions,
            research=research,
            cross_checks=cross_payload,
            five_cs=rebuild_five_cs(score),
            recommendation=recommendation,
            swot=score.swot or {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        )

        report = Report(case_id=case.id, report_type="cam", format="docx", sections=sections)
        session.add(report)
        await session.commit()
        await session.refresh(report)

        docx_bytes = export_cam_docx(case.company_name, sections)
        pdf_bytes = export_cam_pdf(case.company_name, sections)
        report.stored_path = storage.save_report_file(case.id, report.id, "docx", docx_bytes)
        pdf_relative_path = storage.save_report_file(case.id, report.id, "pdf", pdf_bytes)
        case.status = "report_ready"
        await session.commit()
        await session.refresh(report)
        return (
            report,
            storage.absolute_path(report.stored_path),
            storage.absolute_path(pdf_relative_path),
        )


async def main() -> None:
    backend = "docling_remote"
    await init_db()
    case = await create_case()
    print(f"created_case={case.id}", flush=True)

    staged: list[tuple[str, Document]] = []
    for expected_category, source_path in SAMPLE_DOCUMENTS:
        if not source_path.exists():
            raise FileNotFoundError(f"Missing sample document: {source_path}")
        document = await stage_document(case.id, source_path)
        staged.append((expected_category, document))
        print(
            f"staged_document file={document.original_filename} id={document.id} expected={expected_category}",
            flush=True,
        )

    semaphore = asyncio.Semaphore(4)

    async def _run(expected_category: str, document_id: str) -> ProcessSummary:
        async with semaphore:
            return await process_document_job(case.id, document_id, expected_category, backend)

    started = time.perf_counter()
    results = await asyncio.gather(*[_run(expected, document.id) for expected, document in staged])
    total_process_seconds = round(time.perf_counter() - started, 3)
    print(f"processing_total_seconds={total_process_seconds}", flush=True)
    for item in results:
        print(
            "document_result "
            f"id={item.document_id} "
            f"file={item.original_filename!r} "
            f"expected={item.expected_category} "
            f"auto={item.auto_category} "
            f"user={item.user_category} "
            f"pages={item.total_pages} "
            f"status={item.processing_status} "
            f"seconds={item.elapsed_seconds}",
            flush=True,
        )

    async with SessionLocal() as session:
        case = await session.get(Case, case.id)
        if case is None:
            raise RuntimeError("Case vanished during analysis.")
        print("running_analysis=true", flush=True)
        score = await run_case_analysis(session, case, [])
        print("analysis_complete=true", flush=True)

    report, docx_path, pdf_path = await generate_report(case.id, score)

    async with SessionLocal() as session:
        extraction_count = (
            await session.execute(
                select(Extraction).join(Document, Document.id == Extraction.document_id).where(Document.case_id == case.id)
            )
        ).scalars().all()
        research_count = (await session.execute(select(ResearchItem).where(ResearchItem.case_id == case.id))).scalars().all()
        cross_count = (await session.execute(select(CrossVerification).where(CrossVerification.case_id == case.id))).scalars().all()

    print(f"report_id={report.id}", flush=True)
    print(f"report_docx={docx_path}", flush=True)
    print(f"report_pdf={pdf_path}", flush=True)
    print(f"extractions={len(extraction_count)}", flush=True)
    print(f"research_items={len(research_count)}", flush=True)
    print(f"cross_checks={len(cross_count)}", flush=True)
    print(f"overall_score={score.overall_score}", flush=True)
    print(f"risk_grade={score.risk_grade}", flush=True)
    print(f"recommendation={score.recommendation}", flush=True)
    print(f"recommended_amount_crore={score.recommended_amount_crore}", flush=True)
    print(f"recommended_rate_percent={score.recommended_rate_percent}", flush=True)
    print(f"recommended_tenure_months={score.recommended_tenure_months}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
