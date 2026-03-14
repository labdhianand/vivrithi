from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DATE_PATTERNS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
]


def _is_spanning_row(row: list[str], width: int) -> bool:
    if width <= 2:
        return False
    non_empty = [cell for cell in row if cell.strip()]
    if len(non_empty) == 1:
        return True
    if len(non_empty) > 1 and len(set(cell.strip() for cell in non_empty)) == 1:
        return True
    return False


def _render_markdown_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    header = rows[0]
    divider = ["---"] * width
    body = rows[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(divider) + " |"]
    for row in body:
        padded = row + [""] * (width - len(row))
        lines.append("| " + " | ".join(padded) + " |")
    return lines


def table_to_markdown(rows: list[list[str | None]]) -> str:
    cleaned = [[(cell or "").strip() for cell in row] for row in rows if row]
    if not cleaned:
        return ""
    width = max(len(row) for row in cleaned)
    normalized = [row + [""] * (width - len(row)) for row in cleaned]
    parts: list[str] = []
    table_rows: list[list[str]] = []
    for row in normalized:
        if _is_spanning_row(row, width):
            if table_rows:
                parts.extend(_render_markdown_table(table_rows))
                table_rows = []
            label = next((cell for cell in row if cell.strip()), "")
            parts.append(f"\n**{label.strip()}**")
        else:
            table_rows.append(row)
    if table_rows:
        parts.extend(_render_markdown_table(table_rows))
    return "\n".join(parts)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def find_numbers(text: str) -> list[str]:
    return re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?%?", text)


def parse_decimal(value: str | int | float | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    normalized = value.replace(",", "").replace("%", "").replace("Rs.", "").strip()
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def coerce_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    cleaned = clean_text(value)
    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    for match in re.findall(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", cleaned):
        for pattern in ("%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(match, pattern).date()
            except ValueError:
                continue
    return None


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def tokens(value: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", value.lower()) if len(part) > 1}


def confidence_to_band(value: float) -> str:
    if value >= 0.8:
        return "green"
    if value >= 0.5:
        return "amber"
    return "red"

