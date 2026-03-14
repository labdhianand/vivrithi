from __future__ import annotations

from ..models.case import Case
from ..models.research import ResearchItem


def generate_swot(case: Case, five_cs: dict, research: list[ResearchItem], extraction_map: dict) -> dict:
    strengths = [
        {
            "point": f"{case.company_name} shows supportive capital and capacity metrics.",
            "evidence": five_cs["capital"].summary,
            "source": "five_cs",
        },
        {
            "point": "Liquidity position is supported where LCR disclosures are available.",
            "evidence": f"LCR: {extraction_map.get('lcr_ratio') or extraction_map.get('lcr_percent')}",
            "source": "ALM / Financial Results",
        },
    ]
    weaknesses = [
        {
            "point": "Case still depends on external governance and market monitoring.",
            "evidence": five_cs["character"].summary,
            "source": "five_cs",
        }
    ]
    opportunities = [
        {
            "point": f"{case.sector or 'Sector'} demand and funding access could support growth.",
            "evidence": "Sector and market research items were incorporated into Conditions scoring.",
            "source": "research",
        }
    ]
    threats = [
        {
            "point": "Regulatory tightening or sector stress could affect funding costs.",
            "evidence": "; ".join(item.title or "" for item in research[:3]) or "External research monitoring required.",
            "source": "research",
        }
    ]
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
    }

