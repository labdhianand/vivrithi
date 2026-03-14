from __future__ import annotations

from backend.app.models.case import Case
from backend.app.models.document import Document
from backend.app.models.extraction import Extraction
from backend.app.models.research import ResearchItem
from backend.app.services.cam_generator import generate_cam_sections
from backend.app.services.exporter import export_cam_docx, export_cam_pdf
from backend.app.services.five_cs_scorer import CScore


def test_generate_cam_sections_and_export_files() -> None:
    case = Case(company_name="Aavas Financiers Limited", sector="Housing Finance", loan_amount_crore=250)
    documents = [
        Document(original_filename="alm.pdf", user_category="ALM", stored_path="cases/test/alm.pdf"),
        Document(original_filename="rating.pdf", user_category="Borrowing_Profile", stored_path="cases/test/rating.pdf"),
    ]
    extractions = [
        Extraction(schema_field_key="promoter_holding_percent", value="48.95%"),
        Extraction(schema_field_key="promoter_name", value="Aquilo House Pte. Ltd"),
        Extraction(schema_field_key="lcr_ratio", value="151.7%"),
        Extraction(schema_field_key="total_rated_facilities_crore", value="9662.00"),
    ]
    research = [
        ResearchItem(
            category="regulatory",
            title="RBI circular",
            summary="RBI circular tightened liquidity governance expectations for HFCs.",
            impact_description="Regulatory changes can alter funding, compliance, or capital needs.",
        )
    ]
    five_cs = {
        "character": CScore("Character", 62, '{"factors":[{"signal":"Stable governance"}]}', "Stable governance"),
        "capacity": CScore("Capacity", 70, '{"factors":[{"signal":"Healthy operating profile"}]}', "Healthy operating profile"),
        "capital": CScore("Capital", 66, '{"factors":[{"signal":"Adequate capitalization"}]}', "Adequate capitalization"),
        "collateral": CScore("Collateral", 58, '{"factors":[{"signal":"Moderate collateral coverage"}]}', "Moderate collateral coverage"),
        "conditions": CScore("Conditions", 64, '{"factors":[{"signal":"Regulatory watch items present"}]}', "Regulatory watch items present"),
        "overall_score": 64,
        "risk_grade": "BBB",
    }
    recommendation = {
        "recommendation": "approve_with_conditions",
        "risk_grade": "BBB",
        "recommended_amount_crore": 200,
        "recommended_rate_percent": 11.25,
        "recommended_tenure_months": 36,
        "decision_reasoning": "Balanced risk profile with manageable conditions.",
        "key_risks": [{"title": "Regulatory", "detail": "Monitor RBI liquidity governance changes."}],
        "key_strengths": [{"title": "Liquidity", "detail": "Healthy LCR."}],
        "conditions_precedent": [],
        "conditions_subsequent": [],
        "monitoring_covenants": [],
    }
    swot = {
        "strengths": [{"point": "Healthy liquidity", "evidence": "LCR 151.7%"}],
        "weaknesses": [{"point": "Moderate collateral", "evidence": "Coverage remains moderate"}],
        "opportunities": [{"point": "Housing finance growth", "evidence": "Sector demand is resilient"}],
        "threats": [{"point": "Regulatory tightening", "evidence": "RBI circular"}],
    }

    sections = generate_cam_sections(
        case=case,
        documents=documents,
        extractions=extractions,
        research=research,
        cross_checks=[{"check_name": "LCR consistency", "status": "match", "note": "Consistent", "value_a": "151.7%", "value_b": "151.7%"}],
        five_cs=five_cs,
        recommendation=recommendation,
        swot=swot,
    )
    docx_bytes = export_cam_docx(case.company_name, sections)
    pdf_bytes = export_cam_pdf(case.company_name, sections)

    assert sections
    assert sections[0]["title"] == "Executive Summary"
    assert docx_bytes[:2] == b"PK"
    assert pdf_bytes.startswith(b"%PDF")
