from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from ..models.analyst_note import AnalystNote
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from .evidence_refs import build_extraction_index, first_extraction_ref, note_ref, research_ref
from .utils import clamp


@dataclass(slots=True)
class CScore:
    c_name: str
    score: int
    reasoning: str
    summary: str


def _value_map(extractions: list[Extraction]) -> dict[str, Decimal | str | None]:
    mapped: dict[str, Decimal | str | None] = {}
    for extraction in extractions:
        mapped[extraction.schema_field_key] = extraction.value_numeric if extraction.value_numeric is not None else extraction.user_edited_value or extraction.value
    return mapped


def _serialize_factors(factors: list[dict]) -> str:
    for factor in factors:
        refs = factor.get("evidence_refs")
        if isinstance(refs, list):
            factor["evidence_refs"] = [ref for ref in refs if ref]
    return json.dumps({"factors": factors}, ensure_ascii=True)


def _summary(name: str, score: int, factors: list[dict]) -> str:
    if not factors:
        return f"{name} scored {score}/100 based on available documentation."
    head = "; ".join(factor["signal"] for factor in factors[:3])
    return f"{name} scored {score}/100 driven by {head}."


def _research_attr(item: ResearchItem, name: str, default=None):
    return getattr(item, name, default)


def _research_scope(item: ResearchItem) -> str:
    return str(_research_attr(item, "entity_scope", "") or "")


def _research_status(item: ResearchItem) -> str:
    return str(_research_attr(item, "verification_status", "") or "")


def score_character(
    values: dict,
    extraction_index: dict[str, list[Extraction]],
    research: list[ResearchItem],
    notes: list[AnalystNote],
) -> CScore:
    score = 70
    factors: list[dict] = []
    promoter_holding = values.get("promoter_holding_percent")
    shares_pledged = values.get("shares_pledged_percent")
    rating_action = str(values.get("rating_action") or "")

    if isinstance(promoter_holding, Decimal) and promoter_holding > 50:
        score += 5
        factors.append(
            {
                "signal": "Strong promoter holding",
                "impact": 5,
                "evidence": f"{promoter_holding}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "promoter_holding_percent")],
            }
        )
    elif isinstance(promoter_holding, Decimal) and promoter_holding < 20:
        score -= 10
        factors.append(
            {
                "signal": "Low promoter holding",
                "impact": -10,
                "evidence": f"{promoter_holding}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "promoter_holding_percent")],
            }
        )

    if isinstance(shares_pledged, Decimal) and shares_pledged > 75:
        score -= 25
        factors.append(
            {
                "signal": "Critical promoter pledge",
                "impact": -25,
                "evidence": f"CRITICAL: Promoter pledge at {shares_pledged}% - very high default risk indicator",
                "evidence_refs": [first_extraction_ref(extraction_index, "shares_pledged_percent")],
            }
        )
    elif isinstance(shares_pledged, Decimal) and shares_pledged > 50:
        score -= 15
        factors.append(
            {
                "signal": "Elevated promoter pledge",
                "impact": -15,
                "evidence": f"Promoter pledge at {shares_pledged}% - financial stress signal",
                "evidence_refs": [first_extraction_ref(extraction_index, "shares_pledged_percent")],
            }
        )
    elif isinstance(shares_pledged, Decimal) and shares_pledged > 20:
        score -= 8
        factors.append(
            {
                "signal": "High share pledge",
                "impact": -8,
                "evidence": f"{shares_pledged}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "shares_pledged_percent")],
            }
        )

    if "upgrade" in rating_action.lower():
        score += 10
        factors.append(
            {
                "signal": "Recent rating upgrade",
                "impact": 10,
                "evidence": rating_action,
                "evidence_refs": [first_extraction_ref(extraction_index, "rating_action")],
            }
        )
    elif "downgrade" in rating_action.lower():
        score -= 20
        factors.append(
            {
                "signal": "Recent rating downgrade",
                "impact": -20,
                "evidence": rating_action,
                "evidence_refs": [first_extraction_ref(extraction_index, "rating_action")],
            }
        )

    # GST/CIBIL compliance concerns from Indian regulatory research
    gst_cibil_hits = [
        item
        for item in research
        if _research_status(item) in {"verified", "probable"}
        and _research_scope(item) in {"borrower", "promoter"}
        and item.sentiment == "negative"
        and any(
            term in f"{item.title or ''} {item.summary or ''}".lower()
            for term in ["gst", "gstr", "cibil", "wilful defaulter", "npa", "default", "tax evasion"]
        )
    ]
    if gst_cibil_hits:
        impact = -5 * min(len(gst_cibil_hits), 3)
        score += impact
        factors.append(
            {
                "signal": "GST/CIBIL Compliance Concerns",
                "impact": impact,
                "evidence": "; ".join(item.title or "" for item in gst_cibil_hits[:3]),
                "evidence_refs": [research_ref(item) for item in gst_cibil_hits[:3]],
            }
        )

    severe_news = [
        item
        for item in research
        if item.category in {"promoter", "legal"}
        and item.severity in {"high", "critical"}
        and _research_status(item) in {"verified", "probable"}
        and _research_scope(item) in {"borrower", "promoter"}
    ]
    if severe_news:
        impact = -5 * len(severe_news)
        score += impact
        factors.append(
            {
                "signal": "Adverse promoter or legal news",
                "impact": impact,
                "evidence": "; ".join(item.title or "" for item in severe_news[:3]),
                "evidence_refs": [research_ref(item) for item in severe_news[:3]],
            }
        )

    for note in notes:
        if note.affected_c == "Character" and note.risk_adjustment:
            score += note.risk_adjustment
            factors.append(
                {
                    "signal": note.note_type or "Analyst note",
                    "impact": note.risk_adjustment,
                    "evidence": note.content[:160],
                    "evidence_refs": [note_ref(note)],
                }
            )

    final = round(clamp(score))
    return CScore("Character", final, _serialize_factors(factors), _summary("Character", final, factors))


def score_capacity(
    values: dict,
    extraction_index: dict[str, list[Extraction]],
    notes: list[AnalystNote],
) -> CScore:
    score = 65
    factors: list[dict] = []
    pat = values.get("profit_after_tax")
    gnpa = values.get("gnpa_percent")
    nnpa = values.get("nnpa_percent")
    margin = values.get("net_profit_margin")

    if isinstance(pat, Decimal) and pat > 0:
        score += 8
        factors.append(
            {
                "signal": "Positive profitability",
                "impact": 8,
                "evidence": f"PAT {pat}",
                "evidence_refs": [first_extraction_ref(extraction_index, "profit_after_tax")],
            }
        )
    if isinstance(gnpa, Decimal) and gnpa < 2:
        score += 6
        factors.append(
            {
                "signal": "Low GNPA",
                "impact": 6,
                "evidence": f"GNPA {gnpa}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    elif isinstance(gnpa, Decimal) and gnpa > 10:
        score -= 18
        factors.append(
            {
                "signal": "Major gross NPA concern",
                "impact": -18,
                "evidence": f"Gross NPA at {gnpa}% - major credit quality concern",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    elif isinstance(gnpa, Decimal) and gnpa > 5:
        score -= 10
        factors.append(
            {
                "signal": "Elevated GNPA",
                "impact": -10,
                "evidence": f"Gross NPA at {gnpa}% - elevated NPA warrants further scrutiny",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    if isinstance(nnpa, Decimal) and nnpa < 1:
        score += 5
        factors.append(
            {
                "signal": "Contained NNPA",
                "impact": 5,
                "evidence": f"NNPA {nnpa}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "nnpa_percent")],
            }
        )
    if isinstance(margin, Decimal) and margin > 15:
        score += 5
        factors.append(
            {
                "signal": "Healthy margin",
                "impact": 5,
                "evidence": f"Margin {margin}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "net_profit_margin")],
            }
        )

    for note in notes:
        if note.affected_c == "Capacity" and note.risk_adjustment:
            score += note.risk_adjustment
            factors.append(
                {
                    "signal": note.note_type or "Analyst note",
                    "impact": note.risk_adjustment,
                    "evidence": note.content[:160],
                    "evidence_refs": [note_ref(note)],
                }
            )

    final = round(clamp(score))
    return CScore("Capacity", final, _serialize_factors(factors), _summary("Capacity", final, factors))


def score_capital(
    values: dict,
    extraction_index: dict[str, list[Extraction]],
    notes: list[AnalystNote],
) -> CScore:
    score = 60
    factors: list[dict] = []
    crar = values.get("crar_percent")
    debt_equity = values.get("debt_equity_ratio")
    net_worth = values.get("net_worth_lakhs") or values.get("net_worth_crore")

    if isinstance(crar, Decimal) and crar > 25:
        score += 10
        factors.append(
            {
                "signal": "Strong CRAR",
                "impact": 10,
                "evidence": f"CRAR {crar}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "crar_percent")],
            }
        )
    if isinstance(debt_equity, Decimal) and debt_equity < 5:
        score += 6
        factors.append(
            {
                "signal": "Manageable leverage",
                "impact": 6,
                "evidence": f"D/E {debt_equity}",
                "evidence_refs": [first_extraction_ref(extraction_index, "debt_equity_ratio")],
            }
        )
    elif isinstance(debt_equity, Decimal) and debt_equity > 8:
        score -= 10
        factors.append(
            {
                "signal": "High leverage",
                "impact": -10,
                "evidence": f"D/E {debt_equity}",
                "evidence_refs": [first_extraction_ref(extraction_index, "debt_equity_ratio")],
            }
        )
    if isinstance(net_worth, Decimal) and net_worth > 0:
        score += 6
        factors.append(
            {
                "signal": "Positive net worth",
                "impact": 6,
                "evidence": f"Net worth {net_worth}",
                "evidence_refs": [
                    first_extraction_ref(extraction_index, "net_worth_lakhs")
                    or first_extraction_ref(extraction_index, "net_worth_crore")
                ],
            }
        )

    for note in notes:
        if note.affected_c == "Capital" and note.risk_adjustment:
            score += note.risk_adjustment
            factors.append(
                {
                    "signal": note.note_type or "Analyst note",
                    "impact": note.risk_adjustment,
                    "evidence": note.content[:160],
                    "evidence_refs": [note_ref(note)],
                }
            )

    final = round(clamp(score))
    return CScore("Capital", final, _serialize_factors(factors), _summary("Capital", final, factors))


def score_collateral(
    values: dict,
    extraction_index: dict[str, list[Extraction]],
    notes: list[AnalystNote],
) -> CScore:
    score = 58
    factors: list[dict] = []
    gnpa = values.get("gnpa_percent")
    coverage = values.get("provision_coverage_ratio")

    if isinstance(gnpa, Decimal) and gnpa < 2:
        score += 8
        factors.append(
            {
                "signal": "Asset quality supportive",
                "impact": 8,
                "evidence": f"GNPA {gnpa}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    elif isinstance(gnpa, Decimal) and gnpa > 10:
        score -= 12
        factors.append(
            {
                "signal": "Collateral coverage under stress",
                "impact": -12,
                "evidence": f"Gross NPA at {gnpa}% - major credit quality concern",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    elif isinstance(gnpa, Decimal) and gnpa > 5:
        score -= 6
        factors.append(
            {
                "signal": "Asset quality requires scrutiny",
                "impact": -6,
                "evidence": f"Gross NPA at {gnpa}% - elevated NPA warrants further scrutiny",
                "evidence_refs": [first_extraction_ref(extraction_index, "gnpa_percent")],
            }
        )
    if isinstance(coverage, Decimal) and coverage > 40:
        score += 6
        factors.append(
            {
                "signal": "Provision coverage supportive",
                "impact": 6,
                "evidence": f"PCR {coverage}%",
                "evidence_refs": [first_extraction_ref(extraction_index, "provision_coverage_ratio")],
            }
        )

    for note in notes:
        if note.affected_c == "Collateral" and note.risk_adjustment:
            score += note.risk_adjustment
            factors.append(
                {
                    "signal": note.note_type or "Analyst note",
                    "impact": note.risk_adjustment,
                    "evidence": note.content[:160],
                    "evidence_refs": [note_ref(note)],
                }
            )

    final = round(clamp(score))
    return CScore("Collateral", final, _serialize_factors(factors), _summary("Collateral", final, factors))


def score_conditions(
    values: dict,
    extraction_index: dict[str, list[Extraction]],
    research: list[ResearchItem],
    notes: list[AnalystNote],
) -> CScore:
    score = 62
    factors: list[dict] = []
    lcr = values.get("lcr_ratio") or values.get("lcr_percent")

    if isinstance(lcr, Decimal) and lcr > 110:
        score += 8
        factors.append(
            {
                "signal": "Liquidity buffer adequate",
                "impact": 8,
                "evidence": f"LCR {lcr}%",
                "evidence_refs": [
                    first_extraction_ref(extraction_index, "lcr_ratio")
                    or first_extraction_ref(extraction_index, "lcr_percent")
                ],
            }
        )
    borrower_regulatory_hits = [
        item
        for item in research
        if item.category == "regulatory"
        and item.severity in {"high", "critical"}
        and _research_status(item) in {"verified", "probable"}
        and _research_scope(item) == "borrower"
    ]
    contextual_regulatory_hits = [
        item
        for item in research
        if item.category == "regulatory"
        and item.severity in {"medium", "high", "critical"}
        and _research_status(item) in {"verified", "probable", "contextual"}
        and _research_scope(item) in {"sector", "macro"}
    ]
    if borrower_regulatory_hits:
        score -= 10
        factors.append(
            {
                "signal": "Borrower-specific regulatory signal",
                "impact": -10,
                "evidence": "Borrower-matched regulatory developments flagged.",
                "evidence_refs": [research_ref(item) for item in borrower_regulatory_hits[:3]],
            }
        )
    elif contextual_regulatory_hits:
        score -= 4
        factors.append(
            {
                "signal": "Sector or macro regulatory headwind",
                "impact": -4,
                "evidence": "Contextual regulatory developments may tighten operating conditions.",
                "evidence_refs": [research_ref(item) for item in contextual_regulatory_hits[:3]],
            }
        )
    sector_hits = [
        item
        for item in research
        if item.category == "sector"
        and item.sentiment == "negative"
        and _research_status(item) in {"verified", "probable", "contextual"}
        and _research_scope(item) in {"sector", "macro", "borrower"}
    ]
    if sector_hits:
        score -= 5
        factors.append(
            {
                "signal": "Sector outlook mixed",
                "impact": -5,
                "evidence": "Negative sector commentary identified.",
                "evidence_refs": [research_ref(item) for item in sector_hits[:3]],
            }
        )

    for note in notes:
        if note.affected_c == "Conditions" and note.risk_adjustment:
            score += note.risk_adjustment
            factors.append(
                {
                    "signal": note.note_type or "Analyst note",
                    "impact": note.risk_adjustment,
                    "evidence": note.content[:160],
                    "evidence_refs": [note_ref(note)],
                }
            )

    final = round(clamp(score))
    return CScore("Conditions", final, _serialize_factors(factors), _summary("Conditions", final, factors))


def score_to_grade(score: float) -> str:
    if score >= 85:
        return "AAA"
    if score >= 75:
        return "AA"
    if score >= 65:
        return "A"
    if score >= 55:
        return "BBB"
    if score >= 45:
        return "BB"
    if score >= 35:
        return "B"
    if score >= 25:
        return "C"
    return "D"


def score_five_cs(extractions: list[Extraction], research: list[ResearchItem], notes: list[AnalystNote]) -> dict:
    mapped = _value_map(extractions)
    extraction_index = build_extraction_index(extractions)
    character = score_character(mapped, extraction_index, research, notes)
    capacity = score_capacity(mapped, extraction_index, notes)
    capital = score_capital(mapped, extraction_index, notes)
    collateral = score_collateral(mapped, extraction_index, notes)
    conditions = score_conditions(mapped, extraction_index, research, notes)
    overall = (
        character.score * 0.20
        + capacity.score * 0.25
        + capital.score * 0.25
        + collateral.score * 0.15
        + conditions.score * 0.15
    )
    return {
        "character": character,
        "capacity": capacity,
        "capital": capital,
        "collateral": collateral,
        "conditions": conditions,
        "overall_score": round(overall),
        "risk_grade": score_to_grade(overall),
    }
