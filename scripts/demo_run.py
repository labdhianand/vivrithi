from __future__ import annotations

import asyncio
import hashlib
import os
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
SAMPLE_DOCUMENTS = [
    (
        "ALM",
        ROOT / "claude_data" / "Aavas_Financiers" / "ALM" / "Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf",
    ),
    (
        "Shareholding_Pattern",
        ROOT
        / "claude_data"
        / "Aavas_Financiers"
        / "Shareholding_Pattern"
        / "Shareholding_Pattern_Q3_FY26.pdf",
    ),
    (
        "Borrowing_Profile",
        ROOT
        / "claude_data"
        / "Aavas_Financiers"
        / "Borrowing_Profile"
        / "Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf",
    ),
]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def active_value(extraction: Extraction) -> str | None:
    return extraction.user_edited_value or extraction.value


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
        payload[c_name].summary = factors[0]["signal"] if factors else f"{c_name.title()} score {getattr(score, f'{c_name}_score') or 0}"
    return payload


async def ingest_sample_document(session, case: Case, category: str, source_path: Path) -> Document:
    if not source_path.exists():
        raise FileNotFoundError(f"Missing sample document: {source_path}")

    document = Document(
        case_id=case.id,
        original_filename=source_path.name,
        stored_path="pending",
        file_size_bytes=source_path.stat().st_size,
        mime_type="application/pdf",
        sha256_hash=sha256_bytes(source_path.read_bytes()),
        user_category=category,
        classification_status="approved",
        processing_status="pending",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    relative_path = f"cases/{case.id}/documents/{document.id}/{slugify(source_path.name)}"
    absolute_path = storage.absolute_path(relative_path)
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(source_path, absolute_path)
    document.stored_path = relative_path
    await session.commit()
    await session.refresh(document)

    return await process_document(session, case, document)


async def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is required for the demo run.")

    await init_db()

    async with SessionLocal() as session:
        case = Case(
            company_name="Aavas Financiers Limited",
            cin="L65922RJ2011PLC034297",
            sector="Housing Finance",
            subsector="Retail Affordable Housing Finance",
            loan_type="Term Loan",
            loan_amount_crore=Decimal("250.00"),
            loan_tenure_months=36,
            proposed_rate_percent=Decimal("11.25"),
            loan_purpose="On-lending and general corporate purposes",
            status="onboarding",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        print(f"created_case={case.id}", flush=True)

        processed_documents: list[Document] = []
        for category, source_path in SAMPLE_DOCUMENTS:
            print(f"processing_document category={category} file={source_path.name}", flush=True)
            processed_documents.append(await ingest_sample_document(session, case, category, source_path))
            print(
                f"processed_document category={category} status={processed_documents[-1].processing_status}",
                flush=True,
            )

        print("running_analysis=true", flush=True)
        score = await run_case_analysis(session, case, [])
        print("analysis_complete=true", flush=True)

        documents = list((await session.execute(select(Document).where(Document.case_id == case.id))).scalars().all())
        extractions = list(
            (
                await session.execute(
                    select(Extraction).join(Document, Document.id == Extraction.document_id).where(Document.case_id == case.id)
                )
            ).scalars().all()
        )
        research = list((await session.execute(select(ResearchItem).where(ResearchItem.case_id == case.id))).scalars().all())
        cross_checks = list(
            (await session.execute(select(CrossVerification).where(CrossVerification.case_id == case.id))).scalars().all()
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
        print(f"creating_report={report.id}", flush=True)

        docx_bytes = export_cam_docx(case.company_name, sections)
        pdf_bytes = export_cam_pdf(case.company_name, sections)
        report.stored_path = storage.save_report_file(case.id, report.id, "docx", docx_bytes)
        pdf_relative_path = storage.save_report_file(case.id, report.id, "pdf", pdf_bytes)
        case.status = "report_ready"
        await session.commit()
        await session.refresh(report)

        extraction_map = {item.schema_field_key: active_value(item) for item in extractions if active_value(item)}

        print(f"case_id={case.id}")
        print(f"report_id={report.id}")
        print(f"report_docx={storage.absolute_path(report.stored_path)}")
        print(f"report_pdf={storage.absolute_path(pdf_relative_path)}")
        print(f"processed_documents={len(processed_documents)}")
        for document in processed_documents:
            print(
                "document="
                f"{document.original_filename}"
                f" category={document.user_category}"
                f" auto_category={document.auto_category}"
                f" status={document.processing_status}"
            )
        print(f"research_items={len(research)}")
        print(f"cross_checks={len(cross_checks)}")
        print(f"overall_score={score.overall_score}")
        print(f"risk_grade={score.risk_grade}")
        print(f"recommendation={score.recommendation}")
        print(f"recommended_amount_crore={score.recommended_amount_crore}")
        print(f"recommended_rate_percent={score.recommended_rate_percent}")
        print(f"recommended_tenure_months={score.recommended_tenure_months}")
        for key in [
            "lcr_ratio",
            "hqla_total_weighted",
            "total_net_cash_outflows",
            "promoter_holding_percent",
            "public_holding_percent",
            "fpi_holding_percent",
            "promoter_name",
            "long_term_rating",
            "long_term_outlook",
            "rating_action",
            "total_rated_facilities_crore",
        ]:
            print(f"{key}={extraction_map.get(key)}")


if __name__ == "__main__":
    asyncio.run(main())
