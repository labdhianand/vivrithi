from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from ..config import get_settings
from .llm_text import generate_json, has_text_llm
from .types import ClassificationResult

ALLOWED_CATEGORIES = (
    "ALM",
    "Shareholding_Pattern",
    "Borrowing_Profile",
    "Annual_Report",
    "Portfolio_Performance",
    "GST_Returns",
    "Bank_Statement",
)

CATEGORY_ALIASES = {
    "alm": "ALM",
    "asset liability management": "ALM",
    "shareholding pattern": "Shareholding_Pattern",
    "shareholding": "Shareholding_Pattern",
    "borrowing profile": "Borrowing_Profile",
    "credit rating": "Borrowing_Profile",
    "annual report": "Annual_Report",
    "integrated report": "Annual_Report",
    "portfolio performance": "Portfolio_Performance",
    "portfolio cuts": "Portfolio_Performance",
    "financial results": "Portfolio_Performance",
    "gst returns": "GST_Returns",
    "gst return": "GST_Returns",
    "gstr": "GST_Returns",
    "bank statement": "Bank_Statement",
    "bank statements": "Bank_Statement",
    "account statement": "Bank_Statement",
}

CONFIDENCE_ALIASES = {
    "very_high": 0.95,
    "high": 0.9,
    "strong": 0.88,
    "medium": 0.7,
    "moderate": 0.7,
    "low": 0.45,
    "very_low": 0.25,
}


CATEGORY_PATTERNS = {
    "ALM": [
        r"liquidity coverage ratio",
        r"\blcr\b",
        r"high quality liquid assets",
        r"net cash outflows",
    ],
    "Shareholding_Pattern": [
        r"shareholding pattern",
        r"promoter and promoter group",
        r"public shareholder",
        r"table i",
    ],
    "Borrowing_Profile": [
        r"care ratings",
        r"credit rating",
        r"facilities",
        r"outlook",
        r"rated amount",
        r"existing lender details",
        r"lender details",
        r"sanctioned amount",
        r"outstanding amount",
        r"security offered",
        r"borrowing profile",
    ],
    "Annual_Report": [
        r"annual report",
        r"integrated report",
        r"board'?s report",
        r"management discussion",
        r"financial statements for fy",
        r"consolidated financial statements",
        r"letter from the co-founders",
        r"corporate overview",
        r"statutory reports",
    ],
    "Portfolio_Performance": [
        r"financial results",
        r"statement of profit and loss",
        r"gross npa",
        r"capital adequacy",
        r"annexure",
        r"number of loans",
        r"principal outstanding",
        r"write offs in the quarter",
        r"total par",
        r"branch",
        r"district",
        r"portfolio",
    ],
    "GST_Returns": [
        r"\bgstr?\b",
        r"\bgstin\b",
        r"goods and services tax",
        r"input tax credit",
        r"tax liability",
        r"taxable turnover",
        r"filing period",
    ],
    "Bank_Statement": [
        r"bank statement",
        r"account statement",
        r"opening balance",
        r"closing balance",
        r"total credits",
        r"total debits",
        r"average.*balance",
        r"transaction.*summary",
    ],
}

FILENAME_PATTERNS = {
    "ALM": [
        r"\blcr\b",
        r"liquidity",
        r"alm",
        r"coverage_ratio",
    ],
    "Shareholding_Pattern": [
        r"shareholding",
        r"pattern",
        r"regulation[_ -]?31",
    ],
    "Borrowing_Profile": [
        r"credit[_ -]?rating",
        r"rating",
        r"reaffirm",
        r"care",
        r"icra",
        r"crisil",
    ],
    "Annual_Report": [
        r"annual[_ -]?report",
        r"integrated[_ -]?annual[_ -]?report",
        r"\bar\b",
    ],
    "Portfolio_Performance": [
        r"financial[_ -]?result",
        r"financials",
        r"quarterly[_ -]?result",
        r"q[1-4].*fy",
        r"results",
    ],
    "GST_Returns": [
        r"gst",
        r"gstr",
        r"gstin",
    ],
    "Bank_Statement": [
        r"bank[_ -]?statement",
        r"account[_ -]?statement",
        r"statement",
    ],
}

PAGE_SIGNAL_PATTERNS = {
    "ALM": {
        "financial_table": 2.0,
        "narrative": 0.3,
    },
    "Shareholding_Pattern": {
        "financial_table": 1.5,
    },
    "Borrowing_Profile": {
        "cover_letter": 1.4,
        "financial_table": 0.8,
        "narrative": 0.6,
    },
    "Annual_Report": {
        "narrative": 1.8,
        "cover_letter": 0.2,
    },
    "Portfolio_Performance": {
        "financial_table": 1.4,
        "narrative": 0.5,
    },
}

STRONG_SIGNAL_PATTERNS = {
    "ALM": [
        r"liquidity coverage ratio",
        r"\blcr\b",
        r"high quality liquid assets",
        r"net cash outflows",
        r"asset liability management committee",
    ],
    "Shareholding_Pattern": [
        r"shareholding pattern",
        r"regulation 31",
        r"promoter and promoter group",
        r"public shareholder",
    ],
    "Borrowing_Profile": [
        r"credit rating assignment",
        r"credit rating reaffirmation",
        r"care ratings",
        r"rating action",
        r"stable outlook",
    ],
    "Annual_Report": [
        r"annual report",
        r"integrated report",
        r"board'?s report",
        r"management discussion",
        r"statutory reports",
    ],
    "Portfolio_Performance": [
        r"unaudited financial results",
        r"outcome of the board meeting",
        r"statement of profit and loss",
        r"gross npa",
        r"capital adequacy",
    ],
}


def _filename_scores(filename: str | None) -> Counter:
    scores = Counter()
    if not filename:
        return scores
    lowered = Path(filename).name.lower()
    for category, patterns in FILENAME_PATTERNS.items():
        scores[category] += sum(len(re.findall(pattern, lowered)) * 4 for pattern in patterns)
    return scores


def _normalize_text_for_patterns(text: str) -> str:
    return re.sub(
        r"\b(?:[A-Za-z]\s+){2,}[A-Za-z]\b",
        lambda match: match.group(0).replace(" ", ""),
        text,
    )


def _page_signal_scores(page_signal_counts: dict[str, int] | None) -> Counter:
    scores = Counter()
    if not page_signal_counts:
        return scores
    total_pages = sum(page_signal_counts.values()) or 1
    for category, weights in PAGE_SIGNAL_PATTERNS.items():
        for signal, weight in weights.items():
            signal_ratio = page_signal_counts.get(signal, 0) / total_pages
            scores[category] += signal_ratio * weight * 10
    if total_pages >= 40:
        scores["Annual_Report"] += 8
    if total_pages <= 12 and page_signal_counts.get("financial_table", 0) >= max(1, total_pages // 2):
        scores["ALM"] += 2
        scores["Portfolio_Performance"] += 2
    return scores


def _heuristic_classify(
    text: str,
    filename: str | None = None,
    page_signal_counts: dict[str, int] | None = None,
) -> ClassificationResult:
    lowered = _normalize_text_for_patterns(text).lower()
    scores = Counter()
    for category, patterns in CATEGORY_PATTERNS.items():
        scores[category] = sum(len(re.findall(pattern, lowered)) for pattern in patterns)
    scores.update(_filename_scores(filename))
    scores.update(_page_signal_scores(page_signal_counts))
    category, score = scores.most_common(1)[0] if scores else ("Annual_Report", 0)
    total = sum(scores.values()) or 1
    confidence = min(0.98, max(0.25, score / total + 0.2))
    reasoning = ", ".join(f"{cat}={scores[cat]}" for cat in CATEGORY_PATTERNS)
    return ClassificationResult(category=category, confidence=confidence, reasoning=reasoning)


def _normalize_category(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if normalized in ALLOWED_CATEGORIES:
        return normalized
    lowered = normalized.lower().replace("_", " ").replace("-", " ")
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return CATEGORY_ALIASES.get(lowered)


def _normalize_confidence(value: object) -> float | None:
    if isinstance(value, (int, float)):
        confidence = float(value)
        return confidence / 100.0 if confidence > 1.0 else confidence
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("%", "")
    normalized = normalized.replace("very high", "very_high").replace("very low", "very_low")
    if normalized in CONFIDENCE_ALIASES:
        return CONFIDENCE_ALIASES[normalized]
    try:
        confidence = float(normalized)
    except ValueError:
        return None
    return confidence / 100.0 if confidence > 1.0 else confidence


def _strong_signal_classify(text: str, filename: str | None = None) -> ClassificationResult | None:
    lowered = _normalize_text_for_patterns(text).lower()
    filename_lowered = Path(filename).name.lower() if filename else ""

    if "shareholding" in filename_lowered and "pattern" in filename_lowered:
        return ClassificationResult(
            category="Shareholding_Pattern",
            confidence=0.98,
            reasoning="Filename explicitly identifies a shareholding pattern filing.",
        )
    if "annual" in filename_lowered and "report" in filename_lowered:
        return ClassificationResult(
            category="Annual_Report",
            confidence=0.98,
            reasoning="Filename explicitly identifies an annual report.",
        )
    if "credit" in filename_lowered and "rating" in filename_lowered:
        return ClassificationResult(
            category="Borrowing_Profile",
            confidence=0.97,
            reasoning="Filename explicitly identifies a credit rating document.",
        )
    if "liquidity" in filename_lowered or "coverage_ratio" in filename_lowered or re.search(r"\blcr\b", filename_lowered):
        return ClassificationResult(
            category="ALM",
            confidence=0.97,
            reasoning="Filename explicitly identifies an LCR or liquidity disclosure.",
        )
    if "financial_result" in filename_lowered or "financial result" in filename_lowered:
        return ClassificationResult(
            category="Portfolio_Performance",
            confidence=0.96,
            reasoning="Filename explicitly identifies a quarterly financial results document.",
        )

    for category, patterns in STRONG_SIGNAL_PATTERNS.items():
        matches = sum(len(re.findall(pattern, lowered)) for pattern in patterns)
        if matches >= 2:
            return ClassificationResult(
                category=category,
                confidence=0.94,
                reasoning=f"Strong document-specific text signals matched {category}.",
            )
    return None


def _normalize_llm_payload(payload: object) -> ClassificationResult | None:
    if not isinstance(payload, dict):
        return None
    category = _normalize_category(payload.get("category"))
    confidence = _normalize_confidence(payload.get("confidence"))
    if not category or confidence is None:
        return None
    reasoning = payload.get("reasoning")
    return ClassificationResult(
        category=category,
        confidence=max(0.0, min(0.99, confidence)),
        reasoning=reasoning if isinstance(reasoning, str) and reasoning.strip() else "LLM classification",
    )


async def classify_document(
    first_pages_markdown: str,
    *,
    filename: str | None = None,
    page_signal_counts: dict[str, int] | None = None,
) -> ClassificationResult:
    settings = get_settings()
    strong_signal = _strong_signal_classify(first_pages_markdown, filename=filename)
    if strong_signal is not None:
        return strong_signal

    heuristic = _heuristic_classify(
        first_pages_markdown,
        filename=filename,
        page_signal_counts=page_signal_counts,
    )
    if heuristic.confidence >= 0.92:
        return heuristic
    if not has_text_llm():
        return heuristic

    try:
        payload = generate_json(
            (
                "Classify this Indian corporate credit document into exactly one of: "
                "ALM, Shareholding_Pattern, Borrowing_Profile, Annual_Report, "
                "Portfolio_Performance.\n\n"
                "Definitions:\n"
                "- ALM: liquidity coverage ratio, HQLA, net cash outflows, ALM or liquidity disclosures.\n"
                "- Shareholding_Pattern: regulation 31 shareholding tables, promoter/public holdings.\n"
                "- Borrowing_Profile: credit rating letters, sanction letters, lender facilities, debt borrowing details.\n"
                "- Annual_Report: annual or integrated reports with board's report, management discussion, financial statements.\n"
                "- Portfolio_Performance: quarterly financial results, board meeting outcomes, portfolio cuts, GNPA/NNPA/PAR/AUM performance.\n\n"
                "Rules:\n"
                "- Quarterly financial results or board meeting outcome documents must be Portfolio_Performance even if Regulation 52 debt disclosures appear.\n"
                "- Credit rating assignment or reaffirmation letters must be Borrowing_Profile.\n"
                "- Shareholding filings under Regulation 31 must be Shareholding_Pattern.\n"
                "- LCR or liquidity disclosure documents must be ALM.\n"
                "- Annual or integrated reports must be Annual_Report.\n\n"
                "Return strict JSON only with keys category, confidence, reasoning. "
                "confidence must be a numeric value between 0 and 1.\n\n"
                f"Filename: {filename or 'unknown'}\n"
                f"Page signals: {json.dumps(page_signal_counts or {}, ensure_ascii=True)}\n"
                f"Heuristic hint: {heuristic.category} ({heuristic.confidence:.2f})\n\n"
                f"{first_pages_markdown[:4000]}"
            ),
            model=settings.gemini_text_model,
        )
    except Exception:
        return heuristic

    normalized = _normalize_llm_payload(payload)
    return normalized or heuristic


def detect_compound_document(full_markdown: str) -> list[dict]:
    matches: list[dict] = []
    page_markers = re.split(r"<!-- PAGE (\d+) -->", full_markdown)
    for index in range(1, len(page_markers), 2):
        page_number = int(page_markers[index])
        text = page_markers[index + 1]
        heuristic = _heuristic_classify(text)
        if heuristic.confidence >= 0.55:
            matches.append(
                {
                    "page_number": page_number,
                    "category": heuristic.category,
                    "confidence": heuristic.confidence,
                }
            )
    return matches
