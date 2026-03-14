from __future__ import annotations

from collections import defaultdict

from ..extractor import FIELD_ALIASES
from ..utils import tokens
from .types import CandidateSelection, FastPageParse


CATEGORY_PRIOR_PAGES = {
    "ALM": 3,
    "Borrowing_Profile": 4,
    "Shareholding_Pattern": 4,
    "Portfolio_Performance": 5,
    "Annual_Report": 8,
}


def _significant_terms(field: dict) -> set[str]:
    aliases = FIELD_ALIASES.get(field["key"], []) + [field["label"], field["key"].replace("_", " ")]
    words: set[str] = set()
    for alias in aliases:
        words.update(tokens(alias))
    return {word for word in words if word not in {"the", "of", "and", "to", "for", "in", "on"}}


def score_candidate_pages(pages: list[FastPageParse], field: dict) -> CandidateSelection:
    search_terms = _significant_terms(field)
    scores: dict[int, float] = {}
    for page in pages:
        page_tokens = tokens(page.markdown)
        overlap = len(search_terms & page_tokens)
        if overlap == 0 and field["key"] not in page.markdown.lower():
            continue
        score = float(overlap)
        if field["type"] in {"number", "percentage", "currency_lakhs", "currency_crore"} and page.has_tables:
            score += 2.5
        if page.page_number <= 3:
            score += 0.15
        scores[page.page_number] = round(score, 4)
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    selected = [page_number for page_number, score in ordered[:3] if score > 0]
    return CandidateSelection(field_key=field["key"], page_numbers=selected, scores=scores)


def select_candidate_pages(schema: dict, pages: list[FastPageParse]) -> tuple[dict[str, CandidateSelection], list[FastPageParse]]:
    selections: dict[str, CandidateSelection] = {}
    pages_by_number = {page.page_number: page for page in pages}
    selected_page_numbers: set[int] = set()
    for field in schema["fields"]:
        selection = score_candidate_pages(pages, field)
        selections[field["key"]] = selection
        selected_page_numbers.update(selection.page_numbers)

    prior_pages = CATEGORY_PRIOR_PAGES.get(schema["category"], 4)
    selected_page_numbers.update(range(1, min(len(pages), prior_pages) + 1))
    candidate_pages = [pages_by_number[number] for number in sorted(selected_page_numbers) if number in pages_by_number]
    return selections, candidate_pages


def summarize_candidate_load(selections: dict[str, CandidateSelection]) -> dict[int, int]:
    counts = defaultdict(int)
    for selection in selections.values():
        for page_number in selection.page_numbers:
            counts[page_number] += 1
    return dict(sorted(counts.items()))
