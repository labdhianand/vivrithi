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
    "cash_outflow_deposits": ["deposits (for deposit taking companies)", "deposits"],
    "cash_outflow_unsecured_wholesale": ["unsecured wholesale funding"],
    "cash_outflow_secured_wholesale": ["secured wholesale funding", "secured funding"],
    "cash_outflow_credit_facilities": ["credit and liquidity facilities"],
    "cash_outflow_other_contractual": ["other contractual funding obligations"],
    "cash_outflow_other_contingent": ["other contingent funding obligations"],
    "total_cash_outflows_unweighted": ["total cash outflows"],
    "total_cash_outflows_weighted": ["total cash outflows"],
    "cash_inflow_secured_lending": ["secured lending"],
    "cash_inflow_performing_exposures": ["inflows from fully performing exposures", "fully performing exposures"],
    "cash_inflow_other": ["other cash inflows"],
    "total_cash_inflows_unweighted": ["total cash inflows"],
    "total_cash_inflows_weighted": ["total cash inflows"],
    "total_net_cash_outflows": ["total net cash outflows"],
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

LONG_TERM_RATING_PATTERN = (
    r"\b(CARE|ICRA|CRISIL|IND)\s+"
    r"(AAA|AA\+|AA-|AA|A\+|A-|A|BBB\+|BBB-|BBB|BB\+|BB-|BB|B\+|B-|B|C|D)"
    r"(?:\s*;\s*([A-Za-z]+))?"
)

FIELD_PREFERRED_ROW_TEXT: dict[str, list[str]] = {
    "cash_outflow_deposits": ["deposits (for deposit taking companies)"],
    "cash_outflow_unsecured_wholesale": ["unsecured wholesale funding"],
    "cash_outflow_secured_wholesale": ["secured wholesale funding", "secured funding"],
    "cash_outflow_credit_facilities": ["credit and liquidity facilities"],
    "cash_outflow_other_contractual": ["other contractual funding obligations"],
    "cash_outflow_other_contingent": ["other contingent funding obligations"],
    "total_cash_outflows_unweighted": ["total cash outflows"],
    "total_cash_outflows_weighted": ["total cash outflows"],
    "cash_inflow_secured_lending": ["secured lending"],
    "cash_inflow_performing_exposures": ["inflows from fully performing exposures"],
    "cash_inflow_other": ["other cash inflows"],
    "total_cash_inflows_unweighted": ["total cash inflows"],
    "total_cash_inflows_weighted": ["total cash inflows"],
    "total_net_cash_outflows": ["total net cash outflows"],
    "promoter_holding_percent": ["promoter & promoter group", "promoter and promoter group"],
    "public_holding_percent": ["public"],
    "fpi_holding_percent": ["sub-total (b) (2)", "foreign portfolio investors"],
    "foreign_ownership_limit_utilized": ["as on shareholding date"],
}

FIELD_NEGATIVE_ROW_TEXT: dict[str, list[str]] = {
    "public_holding_percent": ["non public", "less than 25 percentage", "public sector undertaking"],
    "fpi_holding_percent": ["category i", "category ii", "category iii"],
}

FIELD_EXACT_ROW_MATCH: dict[str, set[str]] = {
    "cash_outflow_deposits": {"deposits (for deposit taking companies)"},
    "cash_outflow_unsecured_wholesale": {"unsecured wholesale funding"},
    "cash_outflow_secured_wholesale": {"secured wholesale funding", "secured funding"},
    "cash_outflow_credit_facilities": {"credit and liquidity facilities"},
    "cash_outflow_other_contractual": {"other contractual funding obligations"},
    "cash_outflow_other_contingent": {"other contingent funding obligations"},
    "total_cash_outflows_unweighted": {"total cash outflows"},
    "total_cash_outflows_weighted": {"total cash outflows"},
    "cash_inflow_secured_lending": {"secured lending"},
    "cash_inflow_performing_exposures": {"inflows from fully performing exposures"},
    "cash_inflow_other": {"other cash inflows"},
    "total_cash_inflows_unweighted": {"total cash inflows"},
    "total_cash_inflows_weighted": {"total cash inflows"},
    "total_net_cash_outflows": {"total net cash outflows"},
    "hqla_total_unweighted": {"total high quality liquid assets (hqla)", "total hqla"},
    "hqla_total_weighted": {"total high quality liquid assets (hqla)", "total hqla"},
    "lcr_ratio": {"liquidity coverage ratio (%)", "liquidity coverage ratio (%) *", "liquidity coverage ratio"},
    "promoter_holding_percent": {"promoter & promoter group"},
    "public_holding_percent": {"public"},
    "fpi_holding_percent": {"sub-total (b) (2)"},
}

HEURISTIC_PRIORITY_FIELDS = {
    "promoter_name",
    "rating_agency",
    "long_term_rating",
    "long_term_outlook",
    "rating_action",
    "total_rated_facilities_crore",
}

SERIAL_MARKER_WORDS = {"sno", "srno", "serialno", "searialno", "serial"}


def _is_serial_marker(value: str) -> bool:
    compact = re.sub(r"[\s().-]+", "", clean_text(value))
    if not compact:
        return True
    if compact.lower() in SERIAL_MARKER_WORDS:
        return True
    if re.fullmatch(r"\d+", compact):
        return True
    if re.fullmatch(r"[ivxlcdmIVXLCDM]+", compact):
        return True
    if re.fullmatch(r"[A-Z]", compact):
        return True
    return False


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
        if _is_serial_marker(cleaned):
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
        if numbers and not _is_serial_marker(cleaned):
            values.append(numbers[-1])
    return values


def _numeric_cells_with_indices(row: list[str | None]) -> list[tuple[int, str]]:
    values: list[tuple[int, str]] = []
    for index, cell in enumerate(row):
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        numbers = find_numbers(cleaned)
        if numbers and not _is_serial_marker(cleaned):
            values.append((index, numbers[-1]))
    return values


def _percentage_cells(row: list[str | None]) -> list[str]:
    values: list[str] = []
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        values.extend(match for match in re.findall(r"\d[\d,]*(?:\.\d+)?%", cleaned))
    return values


def _percentage_cells_with_indices(row: list[str | None]) -> list[tuple[int, str]]:
    values: list[tuple[int, str]] = []
    for index, cell in enumerate(row):
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        for match in re.findall(r"\d[\d,]*(?:\.\d+)?%", cleaned):
            values.append((index, match))
    return values


def _all_numeric_cells(row: list[str | None]) -> list[str]:
    values: list[str] = []
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        compact = re.sub(r"[\s().-]+", "", cleaned)
        if re.fullmatch(r"\d+", compact) and len(compact) <= 3:
            continue
        values.extend(find_numbers(cleaned))
    return values


def _row_cells(row: list[str | None]) -> list[str]:
    return [clean_text(cell) for cell in row if clean_text(cell)]


def _row_joined_text(row: list[str | None]) -> str:
    return " | ".join(_row_cells(row))


def _max_number_string(values: list[str], minimum: float | None = None) -> str | None:
    best_raw = None
    best_value = None
    for value in values:
        parsed = parse_decimal(value)
        if parsed is None:
            continue
        if minimum is not None and float(parsed) < minimum:
            continue
        if best_value is None or parsed > best_value:
            best_value = parsed
            best_raw = value
    return best_raw


def _first_percentage_string(values: list[str]) -> str | None:
    return values[0] if values else None


def _row_percentage_values(row: list[str | None]) -> list[str]:
    return [value for value in _all_numeric_cells(row) if value.endswith("%")]


def _shareholding_primary_shares(row: list[str | None]) -> str | None:
    integers: list[str] = []
    for value in _all_numeric_cells(row):
        parsed = parse_decimal(value)
        if parsed is None:
            continue
        if "." in value or value.endswith("%"):
            continue
        if float(parsed) <= 0:
            continue
        integers.append(value)
    if not integers:
        return None
    if len(integers) == 1:
        return integers[0]
    first_two = integers[:2]
    return _max_number_string(first_two)


def _first_matching_row(
    pages: list[ParsedPage],
    *patterns: str,
) -> tuple[int, list[str | None]] | None:
    lowered_patterns = tuple(pattern.lower() for pattern in patterns)
    for page in pages:
        for table in page.tables:
            for row in table.rows:
                label = _row_label(row).lower()
                joined = _row_joined_text(row).lower()
                if any(pattern in label or pattern in joined for pattern in lowered_patterns):
                    return page.page_number, row
    return None


def _row_series_values(row: list[str | None]) -> list[str]:
    values: list[str] = []
    started = False
    for cell in row:
        cleaned = clean_text(cell)
        if not cleaned:
            continue
        compact = re.sub(r"[\s().-]+", "", cleaned)
        numeric_values = find_numbers(cleaned)
        if not started:
            if not numeric_values:
                continue
            if re.fullmatch(r"\d+", compact) and len(compact) <= 3:
                continue
            started = True
        values.extend(numeric_values)
    return values


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", clean_text(label).lower()).strip()


def _sum_amounts(amounts: list[str]) -> str | None:
    total = None
    for amount in amounts:
        parsed = parse_decimal(amount)
        if parsed is None:
            continue
        total = parsed if total is None else total + parsed
    return f"{total}" if total is not None else None


def _multiply_amount(value: str, multiplier: int) -> str | None:
    parsed = parse_decimal(value)
    if parsed is None:
        return None
    return f"{parsed * multiplier}"


def _normalize_decimal_string(value: str | None) -> str | None:
    if not value:
        return value
    parsed = parse_decimal(value)
    return f"{parsed}" if parsed is not None else value


def _extract_shareholding_specific_values(
    pages: list[ParsedPage],
) -> dict[str, tuple[str | None, int | None, float, str]]:
    values: dict[str, tuple[str | None, int | None, float, str]] = {}
    promoter_shares_value: str | None = None
    promoter_shares_page: int | None = None
    public_shares_value: str | None = None
    pledge_declared = False
    ndu_declared = False

    for page in pages:
        for table in page.tables:
            for row in table.rows:
                cells = _row_cells(row)
                if not cells:
                    continue
                label = _normalize_label(_row_label(row))
                joined = _normalize_label(_row_joined_text(row))
                numeric_values = _all_numeric_cells(row)
                percentages = _row_percentage_values(row)

                first_cell = _normalize_label(cells[0])
                if len(cells) >= 2:
                    if first_cell == "name of the company":
                        values.setdefault("company_name", (cells[1], page.page_number, 0.99, "shareholding_key_value"))
                    elif first_cell == "scrip code":
                        values.setdefault("scrip_code", (cells[1], page.page_number, 0.99, "shareholding_key_value"))
                    elif first_cell == "nse symbol":
                        values.setdefault("nse_symbol", (cells[1], page.page_number, 0.99, "shareholding_key_value"))
                    elif first_cell == "isin":
                        values.setdefault("isin", (cells[1], page.page_number, 0.99, "shareholding_key_value"))
                    elif "quarter ended" in first_cell:
                        values.setdefault("reporting_quarter", (cells[1], page.page_number, 0.99, "shareholding_key_value"))
                    elif first_cell == "as on shareholding date":
                        foreign_limit = cells[-1]
                        if foreign_limit:
                            suffix = "%" if not foreign_limit.endswith("%") else ""
                            values.setdefault(
                                "foreign_ownership_limit_utilized",
                                (f"{foreign_limit}{suffix}", page.page_number, 0.98, "shareholding_key_value"),
                            )

                if "encumbered under \"pledged\"" in joined or "encumbered under 'pledge'" in joined:
                    pledge_declared = any(cell.lower() == "yes" for cell in cells[1:])
                if "non-disposal undertaking" in joined:
                    ndu_declared = any(cell.lower() == "yes" for cell in cells[1:])

                if label in {
                    "promoter & promoter group",
                    "total shareholding of promoter and promoter group (a)= (a)(1)+(a) (2)",
                    "total shareholding of promoter and promoter group (a)= (a)(1)+(a)(2)",
                }:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["promoter_holding_percent"] = (
                            percentage,
                            page.page_number,
                            0.99,
                            "shareholding_summary",
                        )
                    promoter_shares_value = _shareholding_primary_shares(row)
                    promoter_shares_page = page.page_number
                    if ndu_declared:
                        ndu_candidates = [
                            number
                            for number in numeric_values
                            if parse_decimal(number) is not None
                            and float(parse_decimal(number)) > 1000
                            and number != promoter_shares_value
                        ]
                        ndu_value = ndu_candidates[0] if ndu_candidates else None
                        if ndu_value:
                            values["shares_under_ndu"] = (
                                ndu_value,
                                page.page_number,
                                0.97,
                                "shareholding_summary",
                            )
                    if pledge_declared and percentages:
                        values["shares_pledged_percent"] = (
                            percentages[-1],
                            page.page_number,
                            0.95,
                            "shareholding_summary",
                        )

                if label in {
                    "public",
                    "total public shareholding (b)=(b)(1)+ (b)(2)+(b) (3)+(b)(4)",
                    "total public shareholding (b)=(b)(1)+(b)(2)+(b)(3)+(b)(4)",
                }:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["public_holding_percent"] = (
                            percentage,
                            page.page_number,
                            0.99,
                            "shareholding_summary",
                        )
                    public_shares_value = _shareholding_primary_shares(row)
                    large_ints = [
                        number
                        for number in numeric_values
                        if parse_decimal(number) is not None and float(parse_decimal(number)) > 1000
                    ]
                    esop_candidates = [
                        number
                        for number in large_ints
                        if number != public_shares_value and number != promoter_shares_value
                    ]
                    if esop_candidates:
                        values.setdefault(
                            "esop_outstanding",
                            (esop_candidates[0], page.page_number, 0.9, "shareholding_summary"),
                        )

                if "sub-total (b)(1)" in label or "sub-total (b) (1)" in label:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["dii_holding_percent"] = (percentage, page.page_number, 0.96, "shareholding_subtotal")

                if "sub-total (b)(2)" in label or "sub-total (b) (2)" in label:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["fpi_holding_percent"] = (percentage, page.page_number, 0.98, "shareholding_subtotal")

                if "sub-total (b)(4)" in label or "sub-total (b) (4)" in label:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["retail_holding_percent"] = (percentage, page.page_number, 0.96, "shareholding_subtotal")

                if "mutual funds" in label:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["mutual_fund_holding_percent"] = (
                            percentage,
                            page.page_number,
                            0.96,
                            "shareholding_detail",
                        )

                if "insurance companies" in label:
                    percentage = _first_percentage_string(percentages)
                    if percentage:
                        values["insurance_holding_percent"] = (
                            percentage,
                            page.page_number,
                            0.96,
                            "shareholding_detail",
                        )

    if promoter_shares_value:
        values["promoter_shares"] = (promoter_shares_value, promoter_shares_page, 0.97, "shareholding_summary")
    if promoter_shares_value and public_shares_value:
        promoter_decimal = parse_decimal(promoter_shares_value)
        public_decimal = parse_decimal(public_shares_value)
        if promoter_decimal is not None and public_decimal is not None:
            total = promoter_decimal + public_decimal
            values["total_shares"] = (f"{total}", promoter_shares_page, 0.97, "shareholding_summary")
    return values


def _extract_borrowing_specific_values(
    pages: list[ParsedPage],
    page_lines: dict[int, list[str]],
) -> dict[str, tuple[str | None, int | None, float, str]]:
    values: dict[str, tuple[str | None, int | None, float, str]] = {}
    bank_summary_amount: str | None = None
    bank_summary_page: int | None = None
    ncd_amounts: list[str] = []
    cp_amount: str | None = None
    cp_page: int | None = None
    term_total: str | None = None
    term_total_page: int | None = None
    fund_total: str | None = None
    fund_total_page: int | None = None
    lender_rows: list[dict[str, Any]] = []

    for page in pages:
        for table in page.tables:
            for row in table.rows:
                cells = _row_cells(row)
                if not cells:
                    continue
                label = _normalize_label(_row_label(row))
                joined = _normalize_label(_row_joined_text(row))
                numeric_values = _all_numeric_cells(row)
                amount = _max_number_string(numeric_values, minimum=1.0)

                if "date:" in joined or joined.startswith("date"):
                    date_value = _extract_date_from_line(" ".join(cells))
                    if date_value:
                        values.setdefault("rating_date", (date_value, page.page_number, 0.9, "borrowing_letter_date"))

                rating_match = re.search(r"\b(CARE|ICRA|CRISIL|IND)\s+[A-Z0-9+\-]+(?:\s*;\s*[A-Za-z]+)?", " ".join(cells))
                if rating_match and "commercial paper" in joined:
                    values["short_term_rating"] = (clean_text(rating_match.group(0)), page.page_number, 0.97, "borrowing_summary")

                if "bank facilities" in joined and amount:
                    bank_summary_amount = amount
                    bank_summary_page = page.page_number
                elif ("non-convertible debentures" in joined or "(ncd)" in joined) and amount:
                    ncd_amounts.append(amount)
                elif ("commercial paper" in joined or "(cp)" in joined) and amount:
                    cp_amount = amount
                    cp_page = page.page_number

                if label == "total" and amount:
                    if any(keyword in joined for keyword in ["hdfc bank", "axis bank", "state bank", "kotak", "lender"]):
                        fund_total = amount
                        fund_total_page = page.page_number
                    elif page.page_number >= 5 and term_total is None:
                        term_total = amount
                        term_total_page = page.page_number

                if len(cells) >= 3 and page.page_number >= 5:
                    lender_name = cells[1] if len(cells) > 1 else ""
                    if lender_name and lender_name.lower() not in {"total", "name of bank / lender"}:
                        candidate_amount = None
                        for cell in reversed(cells):
                            if parse_decimal(cell) is not None:
                                candidate_amount = cell
                                break
                        if candidate_amount:
                            facility_type = "Term Loan"
                            remarks = cells[3] if len(cells) > 3 else ""
                            if "fund" in remarks.lower():
                                facility_type = "Fund-Based Limit"
                            lender_rows.append(
                                {
                                    "lender_name": lender_name,
                                    "amount_crore": float(parse_decimal(candidate_amount)),
                                    "facility_type": facility_type,
                                }
                            )

    if not values.get("rating_date"):
        for page_number, lines in page_lines.items():
            for line in lines[:20]:
                lowered = line.lower()
                if "date:" not in lowered and "dated" not in lowered and "december" not in lowered and "june" not in lowered:
                    continue
                date_value = _extract_date_from_line(line)
                if date_value:
                    values["rating_date"] = (date_value, page_number, 0.82, "borrowing_header_date")
                    break
            if values.get("rating_date"):
                break

    for page_number, lines in page_lines.items():
        for line in lines:
            match = re.search(
                LONG_TERM_RATING_PATTERN,
                line,
            )
            if not match:
                continue
            values.setdefault(
                "long_term_rating",
                (f"{match.group(1)} {match.group(2)}", page_number, 0.95, "borrowing_rating_line"),
            )
            if match.group(3):
                values.setdefault(
                    "long_term_outlook",
                    (clean_text(match.group(3)), page_number, 0.93, "borrowing_outlook_line"),
                )
            break
        if values.get("long_term_rating"):
            break

    if bank_summary_amount:
        values["total_rated_facilities_crore"] = (
            _normalize_decimal_string(bank_summary_amount),
            bank_summary_page,
            0.98,
            "borrowing_summary",
        )
        values["term_loan_total_crore"] = (
            _normalize_decimal_string(term_total or bank_summary_amount),
            term_total_page or bank_summary_page,
            0.96 if term_total else 0.9,
            "borrowing_detail" if term_total else "borrowing_summary",
        )
    if ncd_amounts:
        values["ncd_total_crore"] = (
            _normalize_decimal_string(_sum_amounts(ncd_amounts)),
            bank_summary_page,
            0.97,
            "borrowing_summary",
        )
    if cp_amount:
        values["cp_total_crore"] = (_normalize_decimal_string(cp_amount), cp_page, 0.97, "borrowing_summary")
    if fund_total:
        values["fund_based_limits_crore"] = (
            _normalize_decimal_string(fund_total),
            fund_total_page,
            0.96,
            "borrowing_detail",
        )
    if lender_rows:
        values["lender_wise_breakdown"] = (
            json.dumps(lender_rows),
            term_total_page or bank_summary_page,
            0.92,
            "borrowing_detail",
        )
    return values


def _extract_financials_specific_values(
    pages: list[ParsedPage],
) -> dict[str, tuple[str | None, int | None, float, str]]:
    values: dict[str, tuple[str | None, int | None, float, str]] = {}
    pending_interest_income = False
    pending_fee_income = False

    for page in pages:
        for table in page.tables:
            header_text = _normalize_label(table.markdown)
            for row in table.rows:
                label = _normalize_label(_row_label(row))
                joined = _normalize_label(_row_joined_text(row))
                series_values = _row_series_values(row)
                if "operations interest income" in joined:
                    pending_interest_income = True
                    pending_fee_income = True
                    continue
                if pending_interest_income and series_values:
                    values.setdefault("interest_income", (series_values[0], page.page_number, 0.9, "financials_statement"))
                    pending_interest_income = False
                    continue
                if pending_fee_income and series_values and "fair value" in joined:
                    values.setdefault("fee_commission_income", (series_values[0], page.page_number, 0.82, "financials_statement"))
                    pending_fee_income = False

                if "revenue from operations" in joined and series_values:
                    values["total_revenue_operations"] = (series_values[0], page.page_number, 0.94, "financials_statement")
                elif "totalincome" in joined or "total income" in joined:
                    if series_values:
                        values["total_income"] = (series_values[0], page.page_number, 0.95, "financials_statement")
                elif "finance costs" in joined and series_values:
                    values["finance_costs"] = (series_values[0], page.page_number, 0.95, "financials_statement")
                elif "total expenses" in joined and series_values:
                    values["total_expenses"] = (series_values[0], page.page_number, 0.95, "financials_statement")
                elif ("profit befere tax" in joined or "profit before tax" in joined) and series_values:
                    values["profit_before_tax"] = (series_values[0], page.page_number, 0.96, "financials_statement")
                elif "profit after tax" in joined and series_values:
                    values["profit_after_tax"] = (series_values[0], page.page_number, 0.96, "financials_statement")
                elif "basic earnings per share" in joined and series_values:
                    values["eps_basic"] = (series_values[0], page.page_number, 0.92, "financials_statement")
                elif "diluted earnings per share" in joined and series_values:
                    values["eps_diluted"] = (series_values[0], page.page_number, 0.92, "financials_statement")
                elif "number of loans" in joined and series_values:
                    values["loan_assignment_count"] = (series_values[0], page.page_number, 0.9, "financials_supplementary")
                elif "aggregate amount" in joined and series_values:
                    converted = _multiply_amount(series_values[0], 10) if "million" in header_text or "million" in joined else series_values[0]
                    if converted:
                        values["loan_assignment_amount_lakhs"] = (
                            converted,
                            page.page_number,
                            0.88,
                            "financials_supplementary",
                        )
    return values


def _schema_specific_values(
    schema: dict,
    pages: list[ParsedPage],
    page_lines: dict[int, list[str]],
) -> dict[str, tuple[str | None, int | None, float, str]]:
    category = schema.get("category")
    if category == "Shareholding_Pattern":
        return _extract_shareholding_specific_values(pages)
    if category == "Borrowing_Profile":
        return _extract_borrowing_specific_values(pages, page_lines)
    if category == "Portfolio_Performance":
        return _extract_financials_specific_values(pages)
    return {}


def _select_numeric_value(field_key: str, numbers: list[str]) -> str | None:
    if not numbers:
        return None
    if field_key.endswith("_unweighted"):
        return numbers[0]
    if field_key.endswith("_weighted"):
        return numbers[-1]
    if field_key.startswith("cash_outflow_") or field_key.startswith("cash_inflow_"):
        return numbers[-1]
    if field_key in {"total_net_cash_outflows", "lcr_ratio"}:
        return numbers[-1]
    return numbers[-1]


def _select_numeric_value_with_index(field_key: str, numbers: list[tuple[int, str]]) -> tuple[str | None, int | None]:
    if not numbers:
        return None, None
    if field_key.endswith("_unweighted"):
        return numbers[0][1], numbers[0][0]
    if field_key.endswith("_weighted"):
        return numbers[-1][1], numbers[-1][0]
    if field_key.startswith("cash_outflow_") or field_key.startswith("cash_inflow_"):
        return numbers[-1][1], numbers[-1][0]
    if field_key in {"total_net_cash_outflows", "lcr_ratio"}:
        return numbers[-1][1], numbers[-1][0]
    return numbers[-1][1], numbers[-1][0]


def _looks_like_date_context(line: str) -> bool:
    lowered = line.lower()
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", lowered):
        return True
    if re.search(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
        lowered,
    ):
        return True
    return any(marker in lowered for marker in ["quarter ended", "period ended", "reporting date", "dated"])


def _excel_column_name(index: int | None) -> str | None:
    if index is None or index < 0:
        return None
    result = ""
    current = index + 1
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_reference(row_index: int, column_index: int | None) -> str | None:
    column_name = _excel_column_name(column_index)
    if column_name is None:
        return None
    return f"{column_name}{row_index + 1}"


def _header_value(table_rows: list[list[str | None]], row_index: int, column_index: int | None) -> str | None:
    if column_index is None or column_index < 0 or row_index <= 0 or not table_rows:
        return None
    header_row = table_rows[0]
    if column_index >= len(header_row):
        return None
    return clean_text(header_row[column_index]) or None


def _sheet_name_for_page(page_number: int, table: ParsedTable, spreadsheet_mode: bool) -> str | None:
    if not spreadsheet_mode:
        return None
    return table.sheet_name or f"Sheet {page_number}"


def _infer_from_tables(
    field: dict,
    pages: list[ParsedPage],
    *,
    spreadsheet_mode: bool = False,
) -> tuple[str | None, int | None, float, str, dict[str, str | None] | None]:
    if field["key"] == "promoter_name":
        return None, None, 0.0, "no_table_match", None
    aliases = FIELD_ALIASES.get(field["key"], []) + [field["label"].lower(), field["key"].replace("_", " ")]
    best_match: tuple[int, ParsedTable, int, list[str | None], int, int] | None = None
    for page in pages:
        for table in page.tables:
            for row_index, row in enumerate(table.rows):
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
                    or score > best_match[4]
                    or (score == best_match[4] and numeric_count > best_match[5])
                ):
                    best_match = (page.page_number, table, row_index, row, score, numeric_count)
    if best_match is None:
        return None, None, 0.0, "no_table_match", None

    page_number, table, row_index, row, score, _numeric_count = best_match
    numbers = _numeric_cells_with_indices(row)
    row_label = _row_label(row)
    if field["type"] in {"number", "percentage", "currency_lakhs", "currency_crore"}:
        percentage_values = _percentage_cells_with_indices(row)
        if field["type"] == "percentage" and percentage_values:
            if "utilized" in field["key"] or "pledged" in field["key"]:
                column_index, value = percentage_values[-1]
            else:
                column_index, value = percentage_values[0]
            return value, page_number, min(0.95, 0.65 + score * 0.05), "table_numeric", {
                "sheet_name": _sheet_name_for_page(page_number, table, spreadsheet_mode),
                "row_label": row_label or None,
                "column_header": _header_value(table.rows, row_index, column_index),
                "cell_reference": _cell_reference(row_index, column_index),
            }
        if not numbers:
            return None, page_number, min(0.98, 0.7 + score * 0.04), "table_blank", {
                "sheet_name": _sheet_name_for_page(page_number, table, spreadsheet_mode),
                "row_label": row_label or None,
                "column_header": None,
                "cell_reference": None,
            }
        value, column_index = _select_numeric_value_with_index(field["key"], numbers)
        return value, page_number, min(0.95, 0.65 + score * 0.05), "table_numeric", {
            "sheet_name": _sheet_name_for_page(page_number, table, spreadsheet_mode),
            "row_label": row_label or None,
            "column_header": _header_value(table.rows, row_index, column_index),
            "cell_reference": _cell_reference(row_index, column_index),
        }
    if field["type"] == "text":
        remaining = [
            (index, clean_text(cell))
            for index, cell in enumerate(row)
            if clean_text(cell) and clean_text(cell) != row_label
        ]
        value_column = remaining[0][0] if remaining else None
        remaining_values = [item[1] for item in remaining]
        value = " | ".join(remaining_values) if remaining_values else row_label
        return value, page_number, min(0.9, 0.55 + score * 0.05), "table_text", {
            "sheet_name": _sheet_name_for_page(page_number, table, spreadsheet_mode),
            "row_label": row_label or None,
            "column_header": _header_value(table.rows, row_index, value_column),
            "cell_reference": _cell_reference(row_index, value_column),
        }
    if field["type"] == "date":
        row_text = " ".join(clean_text(cell) for cell in row if cell)
        value = _extract_date_from_line(row_text)
        return value, page_number, 0.7 if value else 0.0, "table_date", {
            "sheet_name": _sheet_name_for_page(page_number, table, spreadsheet_mode),
            "row_label": row_label or None,
            "column_header": None,
            "cell_reference": None,
        }
    return None, page_number, 0.0, "table_unsupported", None


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
    reverse_month_match = re.search(
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}",
        line,
        re.IGNORECASE,
    )
    if reverse_month_match:
        return reverse_month_match.group(0)
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


def _result_has_signal(result: ExtractionResult | None) -> bool:
    if result is None:
        return False
    if result.value_numeric is not None:
        return True
    return bool(result.value and str(result.value).strip())


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
    if field["key"] == "reporting_date":
        for page_number, lines in page_lines.items():
            for line in lines:
                lowered = line.lower()
                if not any(marker in lowered for marker in ["quarter ended", "period ended", "reporting date", "as on"]):
                    continue
                value = _extract_date_from_line(line)
                if value:
                    return value, page_number, 0.88, "heuristic_reporting_date"
    if field["key"] in {"long_term_rating", "long_term_outlook"}:
        for page_number, lines in page_lines.items():
            for line in lines:
                match = re.search(
                    LONG_TERM_RATING_PATTERN,
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
        if field_type in {"currency_lakhs", "currency_crore"} and _looks_like_date_context(best_line):
            return None, best_page, 0.0, "missing"
        numbers = find_numbers(best_line)
        if not numbers:
            return None, best_page, 0.0, "missing"
        if field_type in {"currency_lakhs", "currency_crore"}:
            numeric_candidates = [parse_decimal(item) for item in numbers]
            if numeric_candidates and all(
                value is not None and 1900 <= float(value) <= 2100 for value in numeric_candidates
            ):
                return None, best_page, 0.0, "missing"
        if field_type == "percentage" and any(value.endswith("%") for value in numbers):
            value = numbers[-1]
        else:
            value = _select_numeric_value(field["key"], numbers)
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
    try:
        payload = generate_json(prompt, model=settings.gemini_text_model)
    except Exception:
        return None
    return payload if isinstance(payload, list) else None


async def extract_with_schema(
    pdf_path: Path,
    document_markdown: str,
    schema: dict,
    pages: list[ParsedPage],
) -> list[ExtractionResult]:
    spreadsheet_mode = pdf_path.suffix.lower() in {".csv", ".xls", ".xlsx"}
    llm_results = await _llm_extract(document_markdown, schema, pages=pages)
    page_lines = {page.page_number: _page_lines(page) for page in pages}
    specific_values = _schema_specific_values(schema, pages, page_lines)
    llm_by_key = {item["key"]: item for item in llm_results or [] if "key" in item}
    results: list[ExtractionResult] = []

    for field in schema["fields"]:
        specific_item = specific_values.get(field["key"])
        if specific_item is not None:
            specific_value, specific_page, specific_conf, specific_method = specific_item
            specific_bbox = _search_bbox_from_parsed_pages(
                pages,
                specific_page,
                [specific_value or "", field["label"], field["key"].replace("_", " ")],
            ) or _search_bbox(
                pdf_path,
                specific_page,
                [specific_value or "", field["label"], field["key"].replace("_", " ")],
            )
            specific_result = ExtractionResult(
                key=field["key"],
                label=field["label"],
                value=specific_value,
                value_type=field["type"],
                value_numeric=parse_decimal(specific_value) if specific_value else None,
                page_number=specific_page,
                confidence=specific_conf,
                bbox=specific_bbox,
                extraction_method=specific_method,
                extraction_note=None,
                sheet_name=None,
                row_label=None,
                column_header=None,
                cell_reference=None,
            )
            if field.get("required") and not _result_has_signal(specific_result):
                results.append(
                    ExtractionResult(
                        key=field["key"],
                        label=field["label"],
                        value=None,
                        value_type=field["type"],
                        value_numeric=None,
                        page_number=specific_page,
                        confidence=0.0,
                        bbox=specific_bbox,
                        extraction_method="missing_required",
                        extraction_note="Required field could not be extracted from the source document.",
                        sheet_name=None,
                        row_label=None,
                        column_header=None,
                        cell_reference=None,
                    )
                )
            else:
                results.append(specific_result)
            continue

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
                    sheet_name=None,
                    row_label=None,
                    column_header=None,
                    cell_reference=None,
                ),
            ))

        table_value, table_page, table_conf, table_method, table_context = _infer_from_tables(
            field,
            pages,
            spreadsheet_mode=spreadsheet_mode,
        )
        if table_value is not None or table_method == "table_blank":
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
                    value_numeric=parse_decimal(table_value) if table_value else None,
                    page_number=table_page,
                    confidence=table_conf,
                    bbox=table_bbox,
                    extraction_method=table_method,
                    extraction_note=None,
                    sheet_name=(table_context or {}).get("sheet_name"),
                    row_label=(table_context or {}).get("row_label"),
                    column_header=(table_context or {}).get("column_header"),
                    cell_reference=(table_context or {}).get("cell_reference"),
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
                        sheet_name=None,
                        row_label=None,
                        column_header=None,
                        cell_reference=None,
                    ),
                ))

        if candidates:
            best = max(candidates, key=lambda c: c[0])
            if field.get("required") and not _result_has_signal(best[1]):
                results.append(
                    ExtractionResult(
                        key=field["key"],
                        label=field["label"],
                        value=None,
                        value_type=field["type"],
                        value_numeric=None,
                        page_number=best[1].page_number,
                        confidence=0.0,
                        bbox=best[1].bbox,
                        extraction_method="missing_required",
                        extraction_note="Required field could not be extracted from the source document.",
                        sheet_name=best[1].sheet_name,
                        row_label=best[1].row_label,
                        column_header=best[1].column_header,
                        cell_reference=best[1].cell_reference,
                    )
                )
            else:
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
                    extraction_method="missing_required" if field.get("required") else "missing",
                    extraction_note=(
                        "Required field could not be extracted from the source document."
                        if field.get("required")
                        else None
                    ),
                    sheet_name=None,
                    row_label=None,
                    column_header=None,
                    cell_reference=None,
                )
            )

    return results
