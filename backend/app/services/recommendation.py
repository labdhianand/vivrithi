from __future__ import annotations

import json
import logging
from decimal import Decimal

from ..models.case import Case
from ..models.research import ResearchItem

logger = logging.getLogger(__name__)


def _factor_refs(score_obj, limit: int = 2) -> list[dict]:
    try:
        payload = json.loads(score_obj.reasoning or "")
    except json.JSONDecodeError:
        return []
    refs: list[dict] = []
    for factor in payload.get("factors", []):
        for ref in factor.get("evidence_refs", []):
            if ref and ref not in refs:
                refs.append(ref)
        if len(refs) >= limit:
            break
    return refs[:limit]


def _research_attr(item: ResearchItem, name: str, default=None):
    return getattr(item, name, default)


def check_hard_stops(research: list[ResearchItem], cross_checks: list[dict]) -> list[str]:
    reasons = []
    if any(
        item.category == "legal"
        and item.severity in {"high", "critical"}
        and _research_attr(item, "verification_status") in {"verified", "probable"}
        and _research_attr(item, "entity_scope") in {"borrower", "promoter"}
        for item in research
    ):
        reasons.append("High severity legal findings present.")
    if any(check["status"] == "mismatch" and check["check_name"] == "Rating Presence" for check in cross_checks):
        reasons.append("Current rating not clearly evidenced.")
    if any(
        item.category == "legal"
        and _research_attr(item, "verification_status") in {"verified", "probable"}
        and _research_attr(item, "entity_scope") in {"borrower", "promoter"}
        and "willful defaulter" in f"{item.title or ''} {item.summary or ''}".lower()
        for item in research
    ):
        reasons.append("Willful defaulter flag detected in RBI/regulatory search.")
    if any(
        check["status"] == "mismatch" and check["check_name"] == "Non-Core Income Concentration"
        for check in cross_checks
    ):
        reasons.append("High non-core income concentration — possible circular trading risk.")
    return reasons


def calculate_eligible_limit(case: Case, overall_score: int) -> Decimal:
    requested = case.loan_amount_crore or Decimal("0")
    if overall_score >= 75:
        return requested
    if overall_score >= 60:
        return requested * Decimal("0.85")
    if overall_score >= 45:
        return requested * Decimal("0.60")
    return Decimal("0")


def calculate_risk_premium(risk_grade: str) -> Decimal:
    mapping = {
        "AAA": Decimal("0.50"),
        "AA": Decimal("1.00"),
        "A": Decimal("1.75"),
        "BBB": Decimal("2.50"),
        "BB": Decimal("3.50"),
        "B": Decimal("5.00"),
        "C": Decimal("7.50"),
        "D": Decimal("9.00"),
    }
    return mapping.get(risk_grade, Decimal("3.00"))


def build_improvement_scenarios(
    five_cs: dict,
    cross_checks: list[dict],
    hard_stops: list[str],
) -> list[dict]:
    scenarios: list[dict] = []
    seen_titles: set[str] = set()

    def _add(title: str, detail: str, priority: str = "medium") -> None:
        if title in seen_titles:
            return
        seen_titles.add(title)
        scenarios.append({"title": title, "detail": detail, "priority": priority})

    if hard_stops:
        if any("legal" in reason.lower() or "defaulter" in reason.lower() for reason in hard_stops):
            _add(
                "Resolve verified legal findings",
                "Provide court-status updates, closure documents, or management clarification for the verified legal issues before reconsideration.",
                "high",
            )
        if any("rating" in reason.lower() for reason in hard_stops):
            _add(
                "Evidence the current rating position",
                "Upload the latest sanction letter, borrowing statement, or rating rationale to confirm the current external credit view.",
                "high",
            )
        if any("circular trading" in reason.lower() or "non-core income" in reason.lower() for reason in hard_stops):
            _add(
                "Substantiate revenue quality",
                "Provide GST and bank-statement reconciliations to rule out circular trading or inflated non-core income.",
                "high",
            )

    mismatch_names = {item["check_name"] for item in cross_checks if item.get("status") == "mismatch"}
    if "GST-Revenue Reasonableness" in mismatch_names:
        _add(
            "Reconcile GST with reported revenue",
            "Submit a borrower-level reconciliation between GST filings, audited revenue, and banking flows.",
        )
    if "Net Worth Consistency" in mismatch_names or "Debt-Equity Ratio Consistency" in mismatch_names:
        _add(
            "Tighten capital evidence",
            "Provide the latest audited net worth, leverage schedule, and any recent capital infusion support.",
        )
    if "LCR Consistency" in mismatch_names or "CRAR Consistency" in mismatch_names:
        _add(
            "Refresh liquidity and capital pack",
            "Upload the latest ALM disclosure and regulatory capital pack to resolve liquidity or capital discrepancies.",
        )

    score_thresholds = {
        "character": (
            60,
            "Strengthen governance comfort",
            "Add verified promoter background, legal clarifications, and board or governance support to improve Character.",
        ),
        "capacity": (
            60,
            "Improve operating visibility",
            "Provide fresher financial performance, utilization commentary, or cash-flow proof-points to strengthen Capacity.",
        ),
        "capital": (
            60,
            "Improve balance-sheet strength",
            "Demonstrate stronger net worth, lower leverage, or committed capital support to improve Capital.",
        ),
        "collateral": (
            55,
            "Enhance collateral package",
            "Provide clearer security cover, collateral valuation, or structural protections to strengthen Collateral.",
        ),
        "conditions": (
            55,
            "Mitigate sector and regulatory risk",
            "Provide evidence of regulatory compliance, funding resilience, and sector-specific mitigants to improve Conditions.",
        ),
    }
    for key, (threshold, title, detail) in score_thresholds.items():
        factor = five_cs[key]
        if factor.score < threshold:
            _add(title, detail, "medium")

    if not scenarios:
        _add(
            "Maintain performance and disclosure discipline",
            "Keep quarterly disclosures, lender updates, and covenant reporting current to preserve the present credit view.",
            "low",
        )

    return scenarios[:5]


def generate_recommendation(
    case: Case,
    five_cs: dict,
    cross_checks: list[dict],
    research: list[ResearchItem],
    ml_prediction: dict | None = None,
) -> dict:
    overall_score = five_cs["overall_score"]

    # Rule-based decision
    if overall_score >= 65:
        rule_decision = "approve"
    elif overall_score >= 45:
        rule_decision = "conditional_approve"
    else:
        rule_decision = "reject"

    # ML-based decision (if available)
    ml_decision = None
    pd_probability = None
    ml_grade = None
    feature_impacts = []
    if ml_prediction:
        ml_decision = ml_prediction.get("ml_decision", "reject")
        pd_probability = ml_prediction.get("pd_probability")
        ml_grade = ml_prediction.get("ml_grade")
        feature_impacts = ml_prediction.get("feature_impacts", [])

    # Reconcile rule-based and ML decisions
    # ML gets 40% weight, rules get 60%
    if ml_decision:
        decision_rank = {"approve": 2, "conditional_approve": 1, "reject": 0}
        rank_to_decision = {2: "approve", 1: "conditional_approve", 0: "reject"}
        rule_rank = decision_rank.get(rule_decision, 0)
        ml_rank = decision_rank.get(ml_decision, 0)
        blended_rank = round(rule_rank * 0.6 + ml_rank * 0.4)
        decision = rank_to_decision.get(blended_rank, "reject")
    else:
        decision = rule_decision

    hard_stops = check_hard_stops(research, cross_checks)
    if hard_stops:
        decision = "reject"
    improvement_scenarios = build_improvement_scenarios(five_cs, cross_checks, hard_stops)

    # Use ML grade if available, else Five Cs grade
    effective_grade = ml_grade or five_cs["risk_grade"]

    recommended_amount = Decimal("0")
    if decision != "reject":
        recommended_amount = min(
            case.loan_amount_crore or Decimal("0"),
            calculate_eligible_limit(case, overall_score),
        )

    base_rate = Decimal("9.00")
    recommended_rate = base_rate + calculate_risk_premium(effective_grade)
    recommended_tenure = case.loan_tenure_months

    strengths = [
        {
            "title": "Capital profile",
            "detail": five_cs["capital"].summary,
            "evidence_refs": _factor_refs(five_cs["capital"]),
        },
        {
            "title": "Operating profile",
            "detail": five_cs["capacity"].summary,
            "evidence_refs": _factor_refs(five_cs["capacity"]),
        },
    ]
    risks = [
        {
            "title": "Governance and external factors",
            "detail": five_cs["character"].summary,
            "evidence_refs": _factor_refs(five_cs["character"]),
        },
        {
            "title": "Market and sector conditions",
            "detail": five_cs["conditions"].summary,
            "evidence_refs": _factor_refs(five_cs["conditions"]),
        },
    ]

    # Add ML-specific insights
    if feature_impacts:
        top_risk_features = [f for f in feature_impacts if f["importance"] > 5][:3]
        if top_risk_features:
            risks.append({
                "title": "ML model risk drivers",
                "detail": "; ".join(
                    f"{f['feature']}: {f['value']} (importance {f['importance']}%)"
                    for f in top_risk_features
                ),
                "evidence_refs": [],
            })

    conditions_precedent = [
        "Submit latest lender-wise borrowing statement.",
        "Provide management representation confirming no material regulatory breach.",
    ]
    conditions_subsequent = [
        "Quarterly submission of ALM and asset quality pack.",
        "Monthly covenant tracking for leverage and liquidity.",
    ]
    monitoring = [
        "Track GNPA and NNPA movement quarterly.",
        "Monitor rating actions and funding mix changes.",
    ]

    # Build detailed reasoning
    reasoning = (
        f"The case is assessed at {overall_score}/100 ({five_cs['risk_grade']}). "
        f"Decision: {decision}. Character {five_cs['character'].score}, Capacity {five_cs['capacity'].score}, "
        f"Capital {five_cs['capital'].score}, Collateral {five_cs['collateral'].score}, "
        f"Conditions {five_cs['conditions'].score}."
    )
    if pd_probability is not None:
        reasoning += (
            f" ML model estimates probability of default at {pd_probability * 100:.2f}% "
            f"(grade: {ml_grade}). "
        )
    if ml_decision and ml_decision != rule_decision:
        reasoning += (
            f"Rule-based engine suggested '{rule_decision}' while ML model suggested "
            f"'{ml_decision}' — blended to '{decision}'. "
        )
    if hard_stops:
        reasoning += "Hard stops: " + "; ".join(hard_stops)

    mismatches = [c for c in cross_checks if c["status"] == "mismatch"]
    if mismatches:
        reasoning += (
            f" Cross-verification flagged {len(mismatches)} discrepancies: "
            + "; ".join(c["check_name"] for c in mismatches)
            + "."
        )

    result = {
        "recommendation": decision,
        "overall_score": overall_score,
        "risk_grade": five_cs["risk_grade"],
        "recommended_amount_crore": (
            recommended_amount.quantize(Decimal("0.01")) if recommended_amount else Decimal("0.00")
        ),
        "recommended_rate_percent": recommended_rate.quantize(Decimal("0.01")),
        "recommended_tenure_months": recommended_tenure,
        "decision_reasoning": reasoning,
        "key_strengths": strengths,
        "key_risks": risks,
        "conditions_precedent": conditions_precedent,
        "conditions_subsequent": conditions_subsequent,
        "monitoring_covenants": monitoring,
        "improvement_scenarios": improvement_scenarios,
    }

    # Attach ML metadata
    if ml_prediction:
        result["ml_prediction"] = {
            "pd_probability": pd_probability,
            "pd_percentage": ml_prediction.get("pd_percentage"),
            "ml_grade": ml_grade,
            "ml_decision": ml_decision,
            "model_confidence": ml_prediction.get("model_confidence"),
            "feature_impacts": feature_impacts[:8],
            "model_metadata": ml_prediction.get("model_metadata"),
        }

    return result
