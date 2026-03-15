from __future__ import annotations

import logging
import re

from .llm_text import generate_json, has_text_llm

logger = logging.getLogger(__name__)

NOTE_SIGNAL_RULES = [
    {
        "pattern": re.compile(r"\b(factory|plant|capacity|utili[sz]ation|production|order book|collections?)\b", re.I),
        "affected_c": "Capacity",
        "sentiment": "negative",
        "risk_adjustment": -8,
        "signal": "Operating capacity concern",
    },
    {
        "pattern": re.compile(r"\b(promoter|governance|board|resignation|integrity|related party|compliance)\b", re.I),
        "affected_c": "Character",
        "sentiment": "negative",
        "risk_adjustment": -7,
        "signal": "Governance concern",
    },
    {
        "pattern": re.compile(r"\b(collateral|security|valuation|title|charge|mortgage)\b", re.I),
        "affected_c": "Collateral",
        "sentiment": "negative",
        "risk_adjustment": -6,
        "signal": "Collateral concern",
    },
    {
        "pattern": re.compile(r"\b(liquidity|alm|funding|cash flow|rollover|refinancing)\b", re.I),
        "affected_c": "Conditions",
        "sentiment": "negative",
        "risk_adjustment": -6,
        "signal": "Liquidity or funding stress",
    },
    {
        "pattern": re.compile(r"\b(capital|net worth|crar|leverage|equity raise)\b", re.I),
        "affected_c": "Capital",
        "sentiment": "positive",
        "risk_adjustment": 5,
        "signal": "Capital support",
    },
    {
        "pattern": re.compile(r"\b(strong|comfortable|healthy|improved|stable|supportive)\b", re.I),
        "affected_c": "Capacity",
        "sentiment": "positive",
        "risk_adjustment": 4,
        "signal": "Positive operating signal",
    },
]


NEGATIVE_PHRASES = [
    "40% capacity",
    "weak collections",
    "delay",
    "stressed",
    "deterioration",
    "high attrition",
    "governance concern",
]
POSITIVE_PHRASES = [
    "improved collections",
    "comfortable liquidity",
    "strong demand",
    "healthy pipeline",
    "supportive management",
]


def interpret_note(content: str, note_type: str | None = None) -> dict:
    text = (content or "").strip()
    lowered = text.lower()
    matched_signals: list[str] = []
    detected_rule = None

    for rule in NOTE_SIGNAL_RULES:
        if rule["pattern"].search(text):
            detected_rule = rule
            matched_signals.append(rule["signal"])
            break

    affected_c = detected_rule["affected_c"] if detected_rule else "Capacity"
    sentiment = detected_rule["sentiment"] if detected_rule else "neutral"
    risk_adjustment = detected_rule["risk_adjustment"] if detected_rule else 0

    if any(phrase in lowered for phrase in NEGATIVE_PHRASES):
        sentiment = "negative"
        risk_adjustment = min(risk_adjustment, -8) if risk_adjustment < 0 else -8
    elif any(phrase in lowered for phrase in POSITIVE_PHRASES):
        sentiment = "positive"
        risk_adjustment = max(risk_adjustment, 5)

    rationale = "No strong signal detected from note content."
    if detected_rule:
        rationale = f"{detected_rule['signal']} mapped to {affected_c}."
    if note_type == "site_visit" and sentiment == "negative":
        risk_adjustment = min(risk_adjustment - 1, -10)
        rationale += " Site visit negatives receive extra weight."

    return {
        "affected_c": affected_c,
        "sentiment": sentiment,
        "risk_adjustment": risk_adjustment,
        "rationale": rationale,
        "signals": matched_signals,
    }


def interpret_note_llm(content: str, note_type: str | None = None) -> dict | None:
    """Use Gemini LLM to interpret analyst note. Returns None on failure."""
    if not has_text_llm():
        return None
    prompt = f"""You are a credit analyst assistant. Interpret the following analyst note for a corporate loan underwriting case.

Note type: {note_type or 'general'}
Note content: {content}

Classify this note into the Five C framework for credit assessment.
Return a JSON object with exactly these fields:
- "affected_c": one of "Character", "Capacity", "Capital", "Collateral", "Conditions" (which C is most impacted)
- "sentiment": one of "negative", "positive", "neutral"
- "risk_adjustment": integer from -15 to +10 (negative = risk increase, positive = risk reduction)
- "rationale": one sentence explaining your classification
- "signals": array of 1-3 short signal labels describing what was detected

Consider Indian credit context: RBI regulations, CIBIL, GST compliance, NPA norms, promoter governance, NBFC/HFC specific risks.
Return ONLY valid JSON, no markdown."""

    try:
        result = generate_json(prompt)
        if not isinstance(result, dict):
            return None
        # Validate required fields
        valid_cs = {"Character", "Capacity", "Capital", "Collateral", "Conditions"}
        affected = result.get("affected_c", "")
        if affected not in valid_cs:
            return None
        risk_adj = int(result.get("risk_adjustment", 0))
        risk_adj = max(-15, min(10, risk_adj))
        sentiment = result.get("sentiment", "neutral")
        if sentiment not in {"negative", "positive", "neutral"}:
            sentiment = "neutral"
        return {
            "affected_c": affected,
            "sentiment": sentiment,
            "risk_adjustment": risk_adj,
            "rationale": str(result.get("rationale", "LLM interpretation")),
            "signals": list(result.get("signals", [])),
        }
    except Exception:
        logger.warning("LLM note interpretation failed, falling back to regex", exc_info=True)
        return None
