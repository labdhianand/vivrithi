from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import fitz

from ..config import get_settings
from .llm_text import generate_json, has_text_llm
from .types import ExtractionResult, ParsedPage
from .utils import clean_text, coerce_json, find_numbers, parse_date, parse_decimal, tokens


FIELD_ALIASES: dict[str, list[str]] = {
    "lcr_ratio": ["liquidity coverage ratio", "lcr"],
    "hqla_total_weighted": ["total weighted value", "total hqla", "high quality liquid assets"],
    "hqla_total_unweighted": ["total unweighted value", "hqla unweighted"],
    "promoter_holding_percent": ["promoter and promoter group", "promoter holding"],
    "public_holding_percent": ["public shareholding", "public holding", "public shareholder"],
    "fpi_holding_percent": ["foreign portfolio investors", "foreign portfolio investor", "fpi", "sub-total (b) (2)"],
    "long_term_rating": ["long term rating", "rating"],
    "long_term_outlook": ["outlook"],
    "rating_action": ["rating action", "reaffirmed", "revised", "upgraded", "downgraded"],
    "total_rated_facilities_crore": ["total rated facilities", "rated amount"],
    "profit_after_tax": ["profit after tax", "pat"],
    "profit_before_tax": ["profit before tax", "pbt"],
    "total_revenue_operations": ["revenue from operations", "total revenue from operations"],
    "net_worth_lakhs": ["net worth"],
    "net_worth_crore": ["net worth"],
    "debt_equity_ratio": ["debt equity ratio", "debt-equity ratio"],
    "gnpa_percent": ["gross npa", "gnpa"],
    "nnpa_percent": ["net npa", "nnpa"],
    "crar_percent": ["capital risk adequacy ratio", "capital adequacy ratio", "crar"],
    "aum_crore": ["assets under management", "aum"],
    "branch_count": ["number of branches", "branches"],
    "employee_count": ["number of employees", "employees"],
    "nim_percent": ["net interest margin", "nim"],
    "reporting_date": ["reporting date", "date"],
    "rating_date": ["rating date", "dated"],
    "reporting_period": ["quarter ended", "period ended", "reporting period"],
    "reporting_quarter": ["quarter ended", "quarter", "reporting quarter"],
    "fiscal_year": ["fy", "fiscal year", "annual report"],
    "promoter_name": ["promoter name", "name of shareholder", "promoter of the company"],
    "nse_symbol": ["symbol", "nse symbol"],
    "isin": ["isin"],
    "foreign_ownership_limit_utilized": ["limits utilized", "foreign ownership", "approved limits"],
}

ENTITY_SUFFIX_PATTERN = r"(?:Limited|Private Limited|Ltd\.?|Pte\. Ltd\.?)"

ANNUAL_CONTEXT_MARKERS = (
    "annual report",
    "performance snapshot",
    "performance review",
    "chief financial officer",
    "company overview",
)

ANNUAL_FIELD_PATTERNS: dict[str, list[tuple[str, int | None]]] = {
    "fiscal_year": [
        (r"annual report\s+(20\d{2}[-–]\d{2})", 1),
        (r"\bfy\s*(20\d{2}[-–]\d{2})", 1),
    ],
    "aum_crore": [
        (r"aum grew by [^.]{0,120}?(?:at|to)\s*`?\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"assets under management \(aum\) reached\s*`\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"([0-9,]+(?:\.\d+)?)\s*crore\s*assets under management\s*\(aum\)", 1),
    ],
    "net_worth_crore": [
        (r"net worth\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"net worth increased[^.]{0,100}?\bto\s*`?\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"([0-9,]+(?:\.\d+)?)\s*crore\s*net worth", 1),
    ],
    "total_revenue_crore": [
        (r"total revenue\s*([0-9,]+(?:\.\d+)?)", 1),
        (r"total income .*?`\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"([0-9,]+(?:\.\d+)?)\s*crore\s*total revenue", 1),
    ],
    "pat_crore": [
        (r"([0-9,]+(?:\.\d+)?)\s*crore\s*profit after tax\s*\(pat\)", 1),
        (r"profit after tax(?:\s*\(pat\))?[^.]{0,140}?\bto\s*`?\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
    ],
    "disbursements_crore": [
        (r"disbursements\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"disbursements stood at\s*`\s*([0-9,]+(?:\.\d+)?)\s*crore", 1),
        (r"([0-9,]+(?:\.\d+)?)\s*crore\s*disbursements", 1),
    ],
    "roe_percent": [
        (r"return on average net worth was\s*([0-9]+(?:\.\d+)?)%", 1),
        (r"([0-9]+(?:\.\d+)?)%\s*roe", 1),
        (r"roe\s*([0-9]+(?:\.\d+)?)%", 1),
    ],
    "roa_percent": [
        (r"return on average total assets \(roa\) stood at\s*([0-9]+(?:\.\d+)?)%", 1),
        (r"([0-9]+(?:\.\d+)?)%\s*roa", 1),
        (r"roa\s*([0-9]+(?:\.\d+)?)%", 1),
    ],
    "nim_percent": [
        (r"net interest margin \(%\).*?stood at\s*([0-9]+(?:\.\d+)?)%", 1),
        (r"([0-9]+(?:\.\d+)?)%\s*net interest margin\s*\(nim\)", 1),
        (r"net interest margin \(nim\)\s*([0-9]+(?:\.\d+)?)%", 1),
    ],
    "spread_percent": [
        (r"spread.*?stood at\s*([0-9]+(?:\.\d+)?)%", 1),
        (r"([0-9]+(?:\.\d+)?)%\s*spread", 1),
    ],
    "eps": [
        (r"basic \(`\)\s*([0-9]+(?:\.\d+)?)", 1),
        (r"([0-9]+(?:\.\d+)?)\s*eps", 1),
        (r"eps\s*([0-9]+(?:\.\d+)?)", 1),
    ],
    "branch_count": [
        (r"([0-9,]+)\s+branches\s+in\s+([0-9,]+)\s+states", 1),
        (r"network of\s*([0-9,]+)\s+branches", 1),
        (r"([0-9,]+)\s*branches", 1),
    ],
    "states_present": [
        (r"([0-9,]+)\s+branches\s+in\s+([0-9,]+)\s+states", 2),
        (r"across\s*([0-9,]+)\s+states", 1),
    ],
    "employee_count": [
        (r"with a\s*([0-9,]+)\+\s+strong team", 1),
        (r"([0-9,]+)\s+employees", 1),
        (r"([0-9,]+)\s*permanent employees", 1),
    ],
    "customer_count": [
        (r"([0-9,]+)\+\s+customers", 1),
    ],
    "housing_loan_percent": [
        (r"home loans represent\s*([0-9]+)%", 1),
    ],
    "non_housing_loan_percent": [
        (r"accounting for\s*([0-9]+)%\s+of total(?:.+?)loan assets", 1),
        (r"mortgage-backed.+?accounting for\s*([0-9]+)%", 1),
    ],
    "auditor_name": [
        (r"m/s\.\s*([A-Za-z &.]+chartered accountants)", 1),
    ],
}

ANNUAL_SNAPSHOT_RULES: dict[str, tuple[str, str, int, str | None]] = {
    "aum_crore": ("assets under management", "prev", 0, None),
    "net_worth_crore": ("net worth", "prev", 1, None),
    "disbursements_crore": ("disbursements", "prev", 0, None),
    "total_revenue_crore": ("total revenue", "prev", 0, None),
    "roe_percent": ("roe", "prev", 1, "%"),
    "pat_crore": ("profit after tax", "prev", 0, None),
    "roa_percent": ("roa", "prev", 1, "%"),
    "nim_percent": ("net interest margin", "same", 0, "%"),
    "eps": ("eps", "same", 1, None),
    "spread_percent": ("spread", "prev", 0, "%"),
    "employee_count": ("permanent employees", "prev", 1, None),
    "branch_count": ("branches", "prev", 1, None),
}

ANNUAL_INLINE_SNAPSHOT_PATTERNS: dict[str, list[tuple[str, str | None]]] = {
    "aum_crore": [(r"([0-9,]+(?:\.\d+)?)\s*crore\s*assets under management\s*\(aum\)", None)],
    "net_worth_crore": [(r"([0-9,]+(?:\.\d+)?)\s*crore\s*net worth", None)],
    "total_revenue_crore": [(r"([0-9,]+(?:\.\d+)?)\s*crore\s*total revenue", None)],
    "pat_crore": [(r"([0-9,]+(?:\.\d+)?)\s*crore\s*profit after tax\s*\(pat\)", None)],
    "disbursements_crore": [(r"([0-9,]+(?:\.\d+)?)\s*crore\s*disbursements", None)],
    "roe_percent": [(r"([0-9]+(?:\.\d+)?)%\s*roe", "%")],
    "roa_percent": [(r"([0-9]+(?:\.\d+)?)%\s*roa", "%")],
    "nim_percent": [(r"([0-9]+(?:\.\d+)?)%\s*net interest margin\s*\(nim\)", "%")],
    "spread_percent": [(r"([0-9]+(?:\.\d+)?)%\s*spread", "%")],
    "eps": [(r"([0-9]+(?:\.\d+)?)\s*eps", None)],
    "employee_count": [(r"([0-9,]+)\s*permanent employees", None)],
    "branch_count": [(r"([0-9,]+)\s*branches", None)],
}

FIELD_PREFERRED_ROW_TEXT: dict[str, list[str]] = {
    "promoter_holding_percent": ["promoter & promoter group", "promoter and promoter group"],
    "public_holding_percent": ["public"],
    "fpi_holding_percent": ["sub-total (b) (2)", "foreign portfolio investors"],
    "foreign_ownership_limit_utilized": ["as on shareholding date"],
}

FIELD_NEGATIVE_ROW_TEXT: dict[str, list[str]] = {
    "public_holding_percent": ["non public", "less than 25 percentage", "public sector undertaking"],
}

FIELD_EXACT_ROW_MATCH: dict[str, set[str]] = {
    "promoter_holding_percent": {"promoter & promoter group"},
    "public_holding_percent": {"public"},
}

HEURISTIC_PRIORITY_FIELDS = {
    "promoter_name",
    "rating_agency",
    "long_term_rating",
    "long_term_outlook",
    "rating_action",
    "total_rated_facilities_crore",
}

SERIAL_PATTERN = re.compile(r"^[\s().ivxIVX\dA-Z-]+$")


def _page_lines(parsed_page: ParsedPage) -> list[str]:
    raw_lines = []
    for line in parsed_page.markdown.splitlines():
        cleaned = clean_text(line)
        if cleaned:
            raw_lines.append(cleaned)
    return raw_lines


def _row_label(row: list[str | None]) -> str:
    textual_cells = []
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        if SERIAL_PATTERN.match(cleaned):
            continue
        if len(find_numbers(cleaned)) == 1 and cleaned.replace("%", "").replace(",", "").isdigit():
            continue
        textual_cells.append(cleaned)
    return textual_cells[0] if textual_cells else clean_text(" ".join(cell or "" for cell in row))


def _numeric_cells(row: list[str | None]) -> list[str]:
    values: list[str] = []
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        numbers = find_numbers(cleaned)
        if numbers and not SERIAL_PATTERN.match(cleaned):
            values.append(numbers[-1])
    return values


def _percentage_cells(row: list[str | None]) -> list[str]:
    values: list[str] = []
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        values.extend(match for match in re.findall(r"\d[\d,]*(?:\.\d+)?%", cleaned))
    return values


def _infer_from_tables(field: dict, pages: list[ParsedPage]) -> tuple[str | None, int | None, float, str]:
    if field["key"] == "promoter_name":
        return None, None, 0.0, "no_table_match"
    aliases = FIELD_ALIASES.get(field["key"], []) + [field["label"].lower(), field["key"].replace("_", " ")]
    best_match: tuple[int, list[str | None], int, int] | None = None
    for page in pages:
        for table in page.tables:
            for row in table.rows:
                label = _row_label(row).lower()
                score = _match_line_score(label, aliases)
                if label in FIELD_EXACT_ROW_MATCH.get(field["key"], set()):
                    score += 20
                for preferred in FIELD_PREFERRED_ROW_TEXT.get(field["key"], []):
                    if preferred in label:
                        score += 6
                for negative in FIELD_NEGATIVE_ROW_TEXT.get(field["key"], []):
                    if negative in label:
                        score -= 4
                numeric_count = len(_numeric_cells(row))
                if field["type"] in {"number", "percentage", "currency_lakhs", "currency_crore"}:
                    score += min(3, numeric_count)
                if score > 0 and (
                    best_match is None
                    or score > best_match[2]
                    or (score == best_match[2] and numeric_count > best_match[3])
                ):
                    best_match = (page.page_number, row, score, numeric_count)
    if best_match is None:
        return None, None, 0.0, "no_table_match"

    page_number, row, score, _numeric_count = best_match
    numbers = _numeric_cells(row)
    if field["type"] in {"number", "percentage", "currency_lakhs", "currency_crore"}:
        percentage_values = _percentage_cells(row)
        if field["type"] == "percentage" and percentage_values:
            if "utilized" in field["key"] or "pledged" in field["key"]:
                value = percentage_values[-1]
            else:
                value = percentage_values[0]
            return value, page_number, min(0.95, 0.65 + score * 0.05), "table_numeric"
        if not numbers:
            return None, page_number, 0.0, "table_missing_numeric"
        if "unweighted" in field["key"] and len(numbers) >= 1:
            value = numbers[0]
        elif "weighted" in field["key"] and len(numbers) >= 1:
            value = numbers[-1]
        else:
            value = numbers[-1]
        return value, page_number, min(0.95, 0.65 + score * 0.05), "table_numeric"
    if field["type"] == "text":
        label = _row_label(row)
        remaining = [clean_text(cell) for cell in row if clean_text(cell) and clean_text(cell) != label]
        value = " | ".join(remaining) if remaining else label
        return value, page_number, min(0.9, 0.55 + score * 0.05), "table_text"
    if field["type"] == "date":
        row_text = " ".join(clean_text(cell) for cell in row if cell)
        value = _extract_date_from_line(row_text)
        return value, page_number, 0.7 if value else 0.0, "table_date"
    return None, page_number, 0.0, "table_unsupported"


def _significant_tokens(value: str) -> set[str]:
    stop_words = {"of", "the", "and", "in", "to", "for", "rs", "crore", "lakhs", "percent"}
    return {token for token in tokens(value) if token not in stop_words}


def _match_line_score(line: str, aliases: list[str]) -> int:
    line_tokens = tokens(line)
    score = 0
    for alias in aliases:
        alias_tokens = _significant_tokens(alias)
        overlap = len(alias_tokens & line_tokens)
        if overlap == len(alias_tokens) and alias_tokens:
            score = max(score, overlap + 3)
        else:
            score = max(score, overlap)
        if alias in line.lower():
            score += 2
    return score


def _extract_date_from_line(line: str) -> str | None:
    match = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", line)
    if match:
        return match.group(0)
    month_match = re.search(
        r"(?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{2,4}",
        line,
        re.IGNORECASE,
    )
    if month_match:
        return month_match.group(0)
    return None


def _annual_page_windows(lines: list[str], size: int = 3) -> list[str]:
    windows: list[str] = []
    for index in range(len(lines)):
        windows.append(" ".join(lines[index : index + size]))
    return windows


def _annual_search_scopes(lines: list[str]) -> list[str]:
    page_text = " ".join(lines)
    scopes = [page_text]
    for size in (3, 6):
        scopes.extend(_annual_page_windows(lines, size=size))
    return scopes


def _infer_annual_snapshot_value(field_key: str, lines: list[str]) -> str | None:
    page_text = " ".join(lines)
    for pattern, suffix in ANNUAL_INLINE_SNAPSHOT_PATTERNS.get(field_key, []):
        match = re.search(pattern, page_text, re.IGNORECASE)
        if not match:
            continue
        value = clean_text(match.group(1))
        if suffix and not value.endswith(suffix):
            value = f"{value}{suffix}"
        return value
    if "performance snapshot" not in page_text.lower():
        return None
    rule = ANNUAL_SNAPSHOT_RULES.get(field_key)
    if rule is None:
        return None
    label, source, number_index, suffix = rule
    for index, line in enumerate(lines):
        if label not in line.lower():
            continue
        source_line = line
        if source == "prev" and index > 0:
            source_line = lines[index - 1]
        numbers = find_numbers(source_line)
        if len(numbers) <= number_index:
            continue
        value = numbers[number_index]
        if suffix and not value.endswith(suffix):
            value = f"{value}{suffix}"
        return value
    return None


def _infer_annual_auditor_name(lines: list[str]) -> str | None:
    search_scopes = _annual_page_windows(lines, size=4) + _annual_page_windows(lines, size=6) + [" ".join(lines)]
    for scope in search_scopes:
        lowered = scope.lower()
        if "m/s." not in lowered:
            continue
        names = re.findall(
            r"M/s\.\s*([A-Za-z][A-Za-z &.]+?)(?=,|\s+Chartered Accountants)",
            scope,
            re.IGNORECASE,
        )
        cleaned_names: list[str] = []
        for name in names:
            cleaned = clean_text(name).rstrip(".,")
            if not cleaned or cleaned in cleaned_names:
                continue
            cleaned_names.append(cleaned)
        if len(cleaned_names) >= 2:
            return " / ".join(cleaned_names[:2])
        if cleaned_names and ("audit & auditors" in lowered or "statutory auditors" in lowered):
            return cleaned_names[0]
    return None


def _coerce_page_number(value: Any) -> int | None:
    try:
        page_number = int(value)
    except (TypeError, ValueError):
        return None
    return page_number if page_number > 0 else None


def _coerce_confidence(value: Any, default: float = 0.75) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bbox(value: Any) -> tuple[float, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    coordinates: list[float] = []
    for item in value[:4]:
        try:
            coordinates.append(float(item))
        except (TypeError, ValueError):
            continue
    return tuple(coordinates) if coordinates else None


def _llm_has_signal(raw_value: Any, value_numeric: Any) -> bool:
    if value_numeric is not None:
        return True
    value = coerce_json(raw_value)
    return bool(value and str(value).strip())


def _extract_text_value(line: str, aliases: list[str]) -> str | None:
    lowered = line.lower()
    for alias in aliases:
        if alias in lowered:
            start = lowered.index(alias) + len(alias)
            candidate = line[start:].lstrip(" :-|")
            if candidate:
                return candidate
    if ":" in line:
        return clean_text(line.split(":", 1)[1])
    return clean_text(line)


def _build_json_value(key: str, page_lines: dict[int, list[str]]) -> str | None:
    data: list[dict[str, Any]] = []
    if key == "top_shareholders":
        for page_number, lines in page_lines.items():
            for line in lines:
                if "%" in line and any(word in line.lower() for word in ["house", "capital", "fund", "ltd", "limited"]):
                    numbers = find_numbers(line)
                    if len(numbers) >= 2:
                        data.append(
                            {
                                "name": re.split(r"\d", line, 1)[0].strip(" |"),
                                "shares": numbers[0],
                                "percent": numbers[-1].replace("%", ""),
                                "page_number": page_number,
                            }
                        )
                if len(data) >= 5:
                    return coerce_json(data)
    if key == "lender_wise_breakdown":
        for page_number, lines in page_lines.items():
            for line in lines:
                if any(token in line.lower() for token in ["bank", "finance", "capital"]) and any(ch.isdigit() for ch in line):
                    numbers = find_numbers(line)
                    data.append(
                        {
                            "lender_name": re.split(r"\d", line, 1)[0].strip(" |"),
                            "facility_type": "facility",
                            "amount_crore": numbers[-1] if numbers else None,
                            "page_number": page_number,
                        }
                    )
                if len(data) >= 10:
                    return coerce_json(data)
    if key == "key_risks_mentioned":
        for page_number, lines in page_lines.items():
            for line in lines:
                lowered = line.lower()
                if any(word in lowered for word in ["risk", "uncertainty", "liquidity", "asset quality"]):
                    data.append({"point": line, "page_number": page_number})
                if len(data) >= 8:
                    return coerce_json(data)
    return coerce_json(data) if data else None


def _search_bbox_from_parsed_pages(
    pages: list[ParsedPage],
    page_number: int | None,
    search_terms: list[str],
) -> tuple[float, float, float, float] | None:
    if page_number is None or not search_terms:
        return None
    page = next((item for item in pages if item.page_number == page_number), None)
    if page is None:
        return None
    normalized_terms = [clean_text(term).lower() for term in search_terms if clean_text(term)]
    if not normalized_terms:
        return None
    best_match: tuple[int, tuple[float, float, float, float] | None] = (-1, None)
    for item in page.bounding_boxes:
        bbox = _coerce_bbox(item.get("bbox"))
        text = clean_text(item.get("text"))
        if bbox is None or not text:
            continue
        lowered = text.lower()
        score = 0
        for term in normalized_terms:
            if term in lowered:
                score = max(score, len(term))
            else:
                overlap = len(_significant_tokens(term) & _significant_tokens(lowered))
                score = max(score, overlap)
        if score > best_match[0]:
            best_match = (score, bbox if len(bbox) >= 4 else None)
    return best_match[1]


def _search_bbox(source_path: Path, page_number: int | None, search_terms: list[str]) -> tuple[float, float, float, float] | None:
    if page_number is None or not search_terms or source_path.suffix.lower() != ".pdf":
        return None
    with fitz.open(source_path) as doc:
        page = doc[page_number - 1]
        rects = []
        for term in search_terms:
            if not term:
                continue
            rects = page.search_for(term, quads=False)
            if rects:
                break
        if not rects:
            return None
        rect = rects[0]
        width = page.rect.width or 1.0
        height = page.rect.height or 1.0
        return (
            round(rect.x0 / width, 6),
            round(rect.y0 / height, 6),
            round(rect.x1 / width, 6),
            round(rect.y1 / height, 6),
        )


def _infer_value(field: dict, page_lines: dict[int, list[str]]) -> tuple[str | None, int | None, float, str]:
    field_type = field["type"]
    aliases = FIELD_ALIASES.get(field["key"], []) + [field["label"].lower(), field["key"].replace("_", " ")]
    annual_context = any(
        any(marker in line.lower() for marker in ANNUAL_CONTEXT_MARKERS)
        for lines in page_lines.values()
        for line in lines
    )
    if annual_context and field["key"] in ANNUAL_FIELD_PATTERNS:
        for page_number, lines in page_lines.items():
            if field["key"] == "auditor_name":
                auditor_name = _infer_annual_auditor_name(lines)
                if auditor_name is not None:
                    return auditor_name, page_number, 0.94, "annual_report_pattern"
            snapshot_value = _infer_annual_snapshot_value(field["key"], lines)
            if snapshot_value is not None:
                return snapshot_value, page_number, 0.95, "annual_report_snapshot"
        for page_number, lines in page_lines.items():
            for page_text in _annual_search_scopes(lines):
                for pattern, group_index in ANNUAL_FIELD_PATTERNS[field["key"]]:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if not match:
                        continue
                    value = clean_text(match.group(group_index or 1))
                    if field_type == "percentage" and not value.endswith("%"):
                        value = f"{value}%"
                    return value, page_number, 0.94, "annual_report_pattern"
    if field["key"] == "rating_agency":
        for page_number, lines in page_lines.items():
            for line in lines:
                match = re.search(
                    r"((?:CARE|ICRA|CRISIL|India Ratings|Acuite|Brickwork)[A-Za-z ]+Limited)",
                    line,
                )
                if match:
                    return clean_text(match.group(1)), page_number, 0.9, "heuristic_rating_agency"
    if field["key"] in {"long_term_rating", "long_term_outlook"}:
        for page_number, lines in page_lines.items():
            for line in lines:
                match = re.search(
                    r"\b(CARE|ICRA|CRISIL|IND)\s+([A-Z0-9+\-]+)\s*;\s*([A-Za-z]+)",
                    line,
                )
                if match:
                    if field["key"] == "long_term_rating":
                        return f"{match.group(1)} {match.group(2)}", page_number, 0.9, "heuristic_rating"
                    return clean_text(match.group(3)), page_number, 0.88, "heuristic_outlook"
    if field["key"] == "rating_action":
        for page_number, lines in page_lines.items():
            actions = re.findall(
                r"\b(Reaffirmed|Upgraded|Downgraded|Assigned|Revised)\b",
                " ".join(lines),
                re.IGNORECASE,
            )
            if actions:
                counts: dict[str, int] = {}
                for action in actions:
                    normalized = action.title()
                    counts[normalized] = counts.get(normalized, 0) + 1
                best_action = max(counts.items(), key=lambda item: item[1])[0]
                return best_action, page_number, 0.87, "heuristic_rating_action"
    if field["key"] == "total_rated_facilities_crore":
        best_amount = None
        best_page = None
        for page_number, lines in page_lines.items():
            page_text = " ".join(lines)
            for amount in re.findall(r"Rs\.\s*([\d,]+(?:\.\d+)?)\s*/?-\s*crore", page_text, re.IGNORECASE):
                numeric = parse_decimal(amount)
                if numeric is not None and (best_amount is None or numeric > best_amount):
                    best_amount = numeric
                    best_page = page_number
        if best_amount is not None:
            return f"{best_amount}", best_page, 0.86, "heuristic_rated_amount"
    if field["key"] == "promoter_name":
        for page_number, lines in page_lines.items():
            for line in lines:
                marker = re.search(r"promoter of the company", line, re.IGNORECASE)
                if marker:
                    left = line[: marker.start()]
                    for fragment in reversed([part.strip() for part in left.split(",") if part.strip()]):
                        if re.search(fr"{ENTITY_SUFFIX_PATTERN}$", fragment):
                            return clean_text(fragment), page_number, 0.92, "heuristic_promoter_name"
        for page_number, lines in page_lines.items():
            for line in lines:
                if "promoter" in line.lower():
                    fallback = re.search(
                        fr"([A-Z][A-Za-z&., ]+{ENTITY_SUFFIX_PATTERN})",
                        line,
                    )
                    if fallback:
                        return clean_text(fallback.group(1)), page_number, 0.75, "heuristic_promoter_name"
    best_line = None
    best_page = None
    best_score = -1
    for page_number, lines in page_lines.items():
        for line in lines:
            score = _match_line_score(line.lower(), aliases)
            if score > best_score:
                best_score = score
                best_line = line
                best_page = page_number
    if field_type == "json":
        json_value = _build_json_value(field["key"], page_lines)
        return json_value, best_page, 0.55 if json_value else 0.0, "heuristic_json"
    if not best_line or best_score <= 0:
        return None, None, 0.0, "missing"
    if field_type == "date":
        value = _extract_date_from_line(best_line)
        return value, best_page, 0.62 if value else 0.0, "heuristic_date"
    if field_type in {"number", "percentage", "currency_lakhs", "currency_crore"}:
        numbers = find_numbers(best_line)
        if not numbers:
            return None, best_page, 0.0, "missing"
        value = numbers[-1]
        return value, best_page, min(0.9, 0.5 + best_score * 0.05), "heuristic_numeric"
    value = _extract_text_value(best_line, aliases)
    return value, best_page, min(0.88, 0.45 + best_score * 0.05), "heuristic_text"


async def _llm_extract(
    document_markdown: str,
    schema: dict,
    pages: list[ParsedPage] | None = None,
) -> list[dict] | None:
    settings = get_settings()
    if not has_text_llm():
        return None
    char_limit = settings.gemini_context_char_limit
    if pages:
        page_numbers = {p.page_number for p in pages}
        filtered_parts: list[str] = []
        for section in document_markdown.split("<!-- PAGE "):
            if not section.strip():
                continue
            try:
                page_num = int(section.split(" ")[0].split("-->")[0])
            except (ValueError, IndexError):
                filtered_parts.append(section)
                continue
            if page_num in page_numbers:
                filtered_parts.append(f"<!-- PAGE {section}")
        context = "\n".join(filtered_parts)[:char_limit]
    else:
        context = document_markdown[:char_limit]
    fields_description = "\n".join(
        f"- {field['key']} ({field['type']}): {field['label']}" for field in schema["fields"]
    )
    prompt = (
        "You are extracting structured data from an Indian financial document "
        "(NBFC/bank filing, credit rating, ALM disclosure, or shareholding pattern).\n\n"
        "Return a JSON array where each element has: key, value, value_numeric, page_number, confidence, bbox.\n\n"
        "Important conventions for Indian financial filings:\n"
        "- Amounts are typically in lakhs or crores (Rs. / INR)\n"
        "- Percentages should include the % symbol\n"
        "- Dates should be in DD-MM-YYYY format\n"
        "- Rating formats: CARE AA; Stable, ICRA A1+, CRISIL AAA/Stable\n\n"
        "Few-shot examples:\n"
        '1. ALM (LCR): {"key":"lcr_ratio","value":"151.7%","value_numeric":151.7,"page_number":1,"confidence":0.95}\n'
        '2. Shareholding: {"key":"promoter_holding_percent","value":"48.95%","value_numeric":48.95,"page_number":2,"confidence":0.93}\n\n'
        f"Fields:\n{fields_description}\n\nDocument:\n{context}"
    )
    payload = generate_json(prompt, model=settings.gemini_text_model)
    return payload if isinstance(payload, list) else None


async def extract_with_schema(
    pdf_path: Path,
    document_markdown: str,
    schema: dict,
    pages: list[ParsedPage],
) -> list[ExtractionResult]:
    llm_results = await _llm_extract(document_markdown, schema, pages=pages)
    page_lines = {page.page_number: _page_lines(page) for page in pages}
    llm_by_key = {item["key"]: item for item in llm_results or [] if "key" in item}
    results: list[ExtractionResult] = []

    for field in schema["fields"]:
        candidates: list[tuple[float, ExtractionResult]] = []

        heur_value, heur_page, heur_conf, heur_method = _infer_value(field, page_lines)
        if heur_value is not None:
            if field["type"] == "date":
                parsed = parse_date(heur_value)
                heur_value = parsed.isoformat() if parsed else heur_value
            heur_bbox = _search_bbox_from_parsed_pages(
                pages,
                heur_page,
                [heur_value or "", field["label"], field["key"].replace("_", " ")],
            ) or _search_bbox(
                pdf_path,
                heur_page,
                [heur_value or "", field["label"], field["key"].replace("_", " ")],
            )
            effective_conf = heur_conf
            if field["key"] in HEURISTIC_PRIORITY_FIELDS:
                effective_conf = heur_conf + 0.05
            candidates.append((
                effective_conf,
                ExtractionResult(
                    key=field["key"],
                    label=field["label"],
                    value=heur_value,
                    value_type=field["type"],
                    value_numeric=parse_decimal(heur_value),
                    page_number=heur_page,
                    confidence=heur_conf,
                    bbox=heur_bbox,
                    extraction_method=heur_method,
                    extraction_note=None,
                ),
            ))

        table_value, table_page, table_conf, table_method = _infer_from_tables(field, pages)
        if table_value is not None:
            if field["type"] == "date":
                parsed = parse_date(table_value)
                table_value = parsed.isoformat() if parsed else table_value
            table_bbox = _search_bbox_from_parsed_pages(
                pages,
                table_page,
                [table_value or "", field["label"], field["key"].replace("_", " ")],
            ) or _search_bbox(
                pdf_path,
                table_page,
                [table_value or "", field["label"], field["key"].replace("_", " ")],
            )
            candidates.append((
                table_conf,
                ExtractionResult(
                    key=field["key"],
                    label=field["label"],
                    value=table_value,
                    value_type=field["type"],
                    value_numeric=parse_decimal(table_value),
                    page_number=table_page,
                    confidence=table_conf,
                    bbox=table_bbox,
                    extraction_method=table_method,
                    extraction_note=None,
                ),
            ))

        llm_item = llm_by_key.get(field["key"])
        if llm_item:
            raw_value = llm_item.get("value")
            llm_page = _coerce_page_number(llm_item.get("page_number"))
            llm_bbox = _coerce_bbox(llm_item.get("bbox"))
            value_numeric = (
                parse_decimal(str(llm_item.get("value_numeric")))
                if llm_item.get("value_numeric") is not None
                else parse_decimal(coerce_json(raw_value))
            )
            if _llm_has_signal(raw_value, value_numeric):
                llm_conf = _coerce_confidence(llm_item.get("confidence"))
                candidates.append((
                    llm_conf,
                    ExtractionResult(
                        key=field["key"],
                        label=field["label"],
                        value=coerce_json(raw_value),
                        value_type=field["type"],
                        value_numeric=value_numeric,
                        page_number=llm_page,
                        confidence=llm_conf,
                        bbox=llm_bbox,
                        extraction_method="gemini",
                        extraction_note=llm_item.get("extraction_note"),
                    ),
                ))

        if candidates:
            best = max(candidates, key=lambda c: c[0])
            results.append(best[1])
        else:
            results.append(
                ExtractionResult(
                    key=field["key"],
                    label=field["label"],
                    value=None,
                    value_type=field["type"],
                    value_numeric=None,
                    page_number=None,
                    confidence=0.0,
                    bbox=None,
                    extraction_method="missing",
                    extraction_note=None,
                )
            )

    return results
