from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from ..config import get_settings
from .llm_text import generate_json, has_text_llm
from .types import ClassificationResult


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


async def classify_document(
    first_pages_markdown: str,
    *,
    filename: str | None = None,
    page_signal_counts: dict[str, int] | None = None,
) -> ClassificationResult:
    settings = get_settings()
    if settings.classification_require_llm and not has_text_llm():
        raise RuntimeError(
            "Document classification requires Gemini. Set GEMINI_API_KEY."
        )
    if not has_text_llm():
        return _heuristic_classify(
            first_pages_markdown,
            filename=filename,
            page_signal_counts=page_signal_counts,
        )

    payload = generate_json(
        (
            "Classify this Indian financial document into exactly one of: "
            "ALM, Shareholding_Pattern, Borrowing_Profile, Annual_Report, "
            "Portfolio_Performance. Use the filename and page signals when relevant. "
            "Return JSON with keys category, confidence, reasoning.\n\n"
            f"Filename: {filename or 'unknown'}\n"
            f"Page signals: {json.dumps(page_signal_counts or {}, ensure_ascii=True)}\n\n"
            f"{first_pages_markdown[:4000]}"
        ),
        model=settings.gemini_text_model,
    )
    try:
        return ClassificationResult(
            category=payload["category"],
            confidence=float(payload["confidence"]),
            reasoning=payload.get("reasoning", "LLM classification"),
        )
    except Exception:
        if settings.classification_require_llm:
            raise RuntimeError("LLM classification failed and heuristic fallback is disabled.")
        return _heuristic_classify(
            first_pages_markdown,
            filename=filename,
            page_signal_counts=page_signal_counts,
        )


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
