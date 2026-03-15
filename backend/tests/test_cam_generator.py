from __future__ import annotations

import json
from decimal import Decimal

from backend.app.models.case import Case
from backend.app.models.document import Document
from backend.app.models.extraction import Extraction
from backend.app.models.research import ResearchItem
from backend.app.services.cam_generator import generate_cam_sections
from backend.app.services.five_cs_scorer import CScore


def _score(summary: str, refs: list[dict]) -> CScore:
    return CScore(
        "Character",
        72,
        json.dumps(
            {
                "factors": [
                    {
                        "signal": summary,
                        "impact": 6,
                        "evidence": summary,
                        "evidence_refs": refs,
                    }
                ]
            }
        ),
        summary,
    )


def test_generate_cam_sections_carries_evidence_refs() -> None:
    case = Case(
        id="case-1",
        company_name="Evidence Demo Limited",
        cin="U00000MH2020PTC000001",
        sector="NBFC",
        loan_amount_crore=Decimal("75.00"),
    )
    document = Document(
        id="doc-1",
        case_id=case.id,
        original_filename="shareholding.pdf",
        user_category="Shareholding_Pattern",
    )
    extraction = Extraction(
        id="ext-1",
        document_id=document.id,
        schema_field_key="promoter_holding_percent",
        field_label="Promoter holding",
        value="63.2%",
        source_page_number=2,
    )
    extraction.document = document
    research = ResearchItem(
        id="research-1",
        case_id=case.id,
        category="sector",
        title="NBFC liquidity outlook stable",
        summary="Sector liquidity remains adequate for top-rated NBFCs.",
        source_url="https://example.com/sector",
        source_name="Example Research",
        impact_description="Stable funding environment.",
        verification_status="contextual",
        entity_scope="sector",
    )
    five_cs = {
        "character": _score(
            "Strong promoter holding",
            [
                {
                    "kind": "extraction",
                    "label": "Promoter holding",
                    "document_id": document.id,
                    "document_name": document.original_filename,
                    "page_number": 2,
                    "extraction_id": extraction.id,
                    "schema_field_key": extraction.schema_field_key,
                }
            ],
        ),
        "capacity": _score("Healthy earnings", []),
        "capital": _score("Positive net worth", []),
        "collateral": _score("Asset quality supportive", []),
        "conditions": _score("Liquidity buffer adequate", []),
    }

    sections = generate_cam_sections(
        case=case,
        documents=[document],
        extractions=[extraction],
        research=[research],
        cross_checks=[],
        five_cs=five_cs,
        recommendation={
            "recommendation": "approve",
            "risk_grade": "A",
            "recommended_amount_crore": Decimal("75.00"),
            "recommended_rate_percent": Decimal("10.75"),
            "recommended_tenure_months": 24,
            "decision_reasoning": "Supportive profile.",
            "key_strengths": [],
            "key_risks": [],
            "conditions_precedent": [],
            "conditions_subsequent": [],
            "monitoring_covenants": [],
        },
        swot={"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
    )

    company_background = next(section for section in sections if section["id"] == "company_background")
    industry = next(section for section in sections if section["id"] == "industry_analysis")
    five_cs_section = next(section for section in sections if section["id"] == "five_cs_assessment")

    assert company_background["evidence_refs"][0]["document_id"] == document.id
    assert industry["evidence_refs"][0]["url"] == "https://example.com/sector"
    assert five_cs_section["evidence_refs"][0]["extraction_id"] == extraction.id
