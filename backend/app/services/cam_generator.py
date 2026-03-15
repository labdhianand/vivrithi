from __future__ import annotations

from collections import defaultdict
import json

from ..models.case import Case
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from .evidence_refs import build_extraction_index, refs_for_keys, research_ref


CAM_SECTIONS = [
    ("executive_summary", "Executive Summary"),
    ("company_background", "Company Background & Promoter Profile"),
    ("industry_analysis", "Industry & Sector Analysis"),
    ("financial_analysis", "Financial Analysis"),
    ("asset_quality", "Asset Quality & Portfolio Analysis"),
    ("liquidity_alm", "Liquidity & ALM Position"),
    ("borrowing_profile", "Borrowing Profile & Credit Rating"),
    ("five_cs_assessment", "Five Cs Credit Assessment"),
    ("secondary_research", "Secondary Research & External Intelligence"),
    ("cross_verification", "Cross-Document Verification"),
    ("risk_matrix", "Risk Matrix"),
    ("swot", "SWOT Analysis"),
    ("recommendation", "Recommendation"),
    ("appendix", "Appendix: Source Provenance"),
]


def _extraction_summary(extractions: list[Extraction]) -> dict[str, str]:
    data = {}
    for extraction in extractions:
        value = extraction.user_edited_value or extraction.value
        if value:
            data[extraction.schema_field_key] = value
    return data


def _factor_refs(score_obj, limit: int = 3) -> list[dict]:
    try:
        payload = json.loads(score_obj.reasoning or "")
    except (AttributeError, json.JSONDecodeError):
        return []
    refs: list[dict] = []
    for factor in payload.get("factors", []):
        for ref in factor.get("evidence_refs", []):
            if ref and ref not in refs:
                refs.append(ref)
        if len(refs) >= limit:
            break
    return refs[:limit]


def _verified_research(research: list[ResearchItem]) -> list[ResearchItem]:
    return [
        item
        for item in research
        if getattr(item, "verification_status", None) in {"verified", "probable", "contextual"}
    ]


def _borrower_research(research: list[ResearchItem]) -> list[ResearchItem]:
    return [
        item
        for item in _verified_research(research)
        if getattr(item, "entity_scope", None) in {"borrower", "promoter"}
    ]


def _contextual_research(research: list[ResearchItem]) -> list[ResearchItem]:
    return [
        item
        for item in _verified_research(research)
        if getattr(item, "entity_scope", None) in {"sector", "macro"}
    ]


def generate_cam_sections(
    case: Case,
    documents: list[Document],
    extractions: list[Extraction],
    research: list[ResearchItem],
    cross_checks: list[dict],
    five_cs: dict,
    recommendation: dict,
    swot: dict,
) -> list[dict]:
    extraction_map = _extraction_summary(extractions)
    extraction_index = build_extraction_index(extractions)
    borrower_research = _borrower_research(research)
    contextual_research = _contextual_research(research)
    verified_research = _verified_research(research)
    docs_by_category = defaultdict(list)
    for document in documents:
        docs_by_category[document.user_category or document.auto_category or "Unclassified"].append(document.original_filename)

    industry_refs = [research_ref(item) for item in contextual_research[:6]]
    secondary_refs = [research_ref(item) for item in verified_research[:10]]
    executive_refs = [
        *_factor_refs(five_cs["capital"], limit=2),
        *_factor_refs(five_cs["character"], limit=2),
    ][:4]

    sections = []
    sections.append(
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "content_markdown": (
                f"### {case.company_name}\n"
                f"- Loan request: Rs. {case.loan_amount_crore or 'N/A'} crore\n"
                f"- Recommendation: {recommendation['recommendation']}\n"
                f"- Risk grade: {recommendation['risk_grade']}\n"
                f"- Key rationale: {recommendation['decision_reasoning']}"
            ),
            "evidence_refs": executive_refs,
        }
    )
    sections.append(
        {
            "id": "company_background",
            "title": "Company Background & Promoter Profile",
            "content_markdown": (
                f"- Sector: {case.sector or 'N/A'}\n"
                f"- CIN: {case.cin or 'N/A'}\n"
                f"- Promoter holding: {extraction_map.get('promoter_holding_percent', 'N/A')}\n"
                f"- Promoter name: {extraction_map.get('promoter_name', 'N/A')}"
            ),
            "evidence_refs": refs_for_keys(
                extraction_index,
                ["promoter_holding_percent", "promoter_name"],
            ),
        }
    )
    sections.append(
        {
            "id": "industry_analysis",
            "title": "Industry & Sector Analysis",
            "content_markdown": "\n".join(
                f"- {item.title}: {item.summary}" for item in contextual_research[:6]
            ) or "- Contextual sector and macro research pending.",
            "evidence_refs": industry_refs,
        }
    )
    sections.append(
        {
            "id": "financial_analysis",
            "title": "Financial Analysis",
            "content_markdown": (
                f"- Revenue from operations: {extraction_map.get('total_revenue_operations', 'N/A')}\n"
                f"- PAT: {extraction_map.get('profit_after_tax', 'N/A')}\n"
                f"- Net worth: {extraction_map.get('net_worth_lakhs', extraction_map.get('net_worth_crore', 'N/A'))}\n"
                f"- D/E ratio: {extraction_map.get('debt_equity_ratio', 'N/A')}"
            ),
            "evidence_refs": refs_for_keys(
                extraction_index,
                [
                    "total_revenue_operations",
                    "total_revenue_crore",
                    "profit_after_tax",
                    "net_worth_lakhs",
                    "net_worth_crore",
                    "debt_equity_ratio",
                ],
            ),
        }
    )
    sections.append(
        {
            "id": "asset_quality",
            "title": "Asset Quality & Portfolio Analysis",
            "content_markdown": (
                f"- GNPA: {extraction_map.get('gnpa_percent', 'N/A')}\n"
                f"- NNPA: {extraction_map.get('nnpa_percent', 'N/A')}\n"
                f"- Provision coverage: {extraction_map.get('provision_coverage_ratio', 'N/A')}"
            ),
            "evidence_refs": refs_for_keys(
                extraction_index,
                ["gnpa_percent", "nnpa_percent", "provision_coverage_ratio"],
            ),
        }
    )
    sections.append(
        {
            "id": "liquidity_alm",
            "title": "Liquidity & ALM Position",
            "content_markdown": (
                f"- LCR: {extraction_map.get('lcr_ratio', extraction_map.get('lcr_percent', 'N/A'))}\n"
                f"- HQLA weighted: {extraction_map.get('hqla_total_weighted', 'N/A')}\n"
                f"- Net cash outflows: {extraction_map.get('total_net_cash_outflows', 'N/A')}"
            ),
            "evidence_refs": refs_for_keys(
                extraction_index,
                ["lcr_ratio", "lcr_percent", "hqla_total_weighted", "total_net_cash_outflows"],
            ),
        }
    )
    sections.append(
        {
            "id": "borrowing_profile",
            "title": "Borrowing Profile & Credit Rating",
            "content_markdown": (
                f"- Long-term rating: {extraction_map.get('long_term_rating', 'N/A')}\n"
                f"- Outlook: {extraction_map.get('long_term_outlook', 'N/A')}\n"
                f"- Total rated facilities: {extraction_map.get('total_rated_facilities_crore', 'N/A')}"
            ),
            "evidence_refs": refs_for_keys(
                extraction_index,
                ["long_term_rating", "long_term_outlook", "total_rated_facilities_crore", "rating_action"],
            ),
        }
    )
    sections.append(
        {
            "id": "five_cs_assessment",
            "title": "Five Cs Credit Assessment",
            "content_markdown": (
                f"- Character: {five_cs['character'].summary}\n"
                f"- Capacity: {five_cs['capacity'].summary}\n"
                f"- Capital: {five_cs['capital'].summary}\n"
                f"- Collateral: {five_cs['collateral'].summary}\n"
                f"- Conditions: {five_cs['conditions'].summary}"
            ),
            "evidence_refs": [
                *_factor_refs(five_cs["character"]),
                *_factor_refs(five_cs["capacity"]),
                *_factor_refs(five_cs["capital"]),
                *_factor_refs(five_cs["collateral"]),
                *_factor_refs(five_cs["conditions"]),
            ][:8],
        }
    )
    sections.append(
        {
            "id": "secondary_research",
            "title": "Secondary Research & External Intelligence",
            "content_markdown": "\n".join(
                [
                    "#### Borrower / Promoter-specific findings",
                    *[
                        f"- [{item.category}] {item.title}: {item.impact_description}"
                        for item in borrower_research[:5]
                    ],
                    "#### Sector / Macro context",
                    *[
                        f"- [{item.category}] {item.title}: {item.impact_description}"
                        for item in contextual_research[:5]
                    ],
                ]
            ) or "- No verified secondary research signals available.",
            "evidence_refs": secondary_refs,
        }
    )
    sections.append(
        {
            "id": "cross_verification",
            "title": "Cross-Document Verification",
            "content_markdown": "\n".join(
                f"- {check['check_name']}: {check['status']} ({check['note']})" for check in cross_checks
            ) or "- No cross-checks generated.",
            "evidence_refs": [
                *refs_for_keys(extraction_index, ["lcr_ratio", "lcr_percent", "net_worth_lakhs", "net_worth_crore"]),
                *refs_for_keys(extraction_index, ["long_term_rating", "total_revenue_operations", "total_revenue_crore"]),
            ][:6],
        }
    )
    sections.append(
        {
            "id": "risk_matrix",
            "title": "Risk Matrix",
            "content_markdown": "\n".join(
                f"- {risk['title']}: {risk['detail']}" for risk in recommendation["key_risks"]
            ),
            "evidence_refs": [
                ref
                for risk in recommendation["key_risks"]
                for ref in (risk.get("evidence_refs") or [])
            ][:6],
        }
    )
    sections.append(
        {
            "id": "swot",
            "title": "SWOT Analysis",
            "content_markdown": "\n".join(
                [
                    "#### Strengths",
                    *[f"- {item['point']} ({item['evidence']})" for item in swot["strengths"]],
                    "#### Weaknesses",
                    *[f"- {item['point']} ({item['evidence']})" for item in swot["weaknesses"]],
                    "#### Opportunities",
                    *[f"- {item['point']} ({item['evidence']})" for item in swot["opportunities"]],
                    "#### Threats",
                    *[f"- {item['point']} ({item['evidence']})" for item in swot["threats"]],
                ]
            ),
            "evidence_refs": secondary_refs[:4],
        }
    )
    sections.append(
        {
            "id": "recommendation",
            "title": "Recommendation",
            "content_markdown": (
                f"- Decision: {recommendation['recommendation']}\n"
                f"- Amount: {recommendation['recommended_amount_crore']}\n"
                f"- Rate: {recommendation['recommended_rate_percent']}\n"
                f"- Tenure: {recommendation['recommended_tenure_months']}\n"
                f"- Reasoning: {recommendation['decision_reasoning']}\n"
                + (
                    "#### What Would Improve the Case\n"
                    + "\n".join(
                        f"- {item['title']}: {item['detail']}"
                        for item in recommendation.get("improvement_scenarios", [])
                    )
                    if recommendation.get("improvement_scenarios")
                    else ""
                )
            ),
            "evidence_refs": executive_refs,
        }
    )
    sections.append(
        {
            "id": "appendix",
            "title": "Appendix: Source Provenance",
            "content_markdown": "\n".join(
                f"- {category}: {', '.join(files)}" for category, files in docs_by_category.items()
            ),
            "evidence_refs": [],
        }
    )
    return sections
