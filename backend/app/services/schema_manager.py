from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..extraction_schemas import DEFAULT_SCHEMAS
from ..models.schema import ExtractionSchema
from .llm_text import generate_json, has_text_llm


def get_default_schema(category: str) -> dict:
    if category not in DEFAULT_SCHEMAS:
        raise KeyError(f"Unsupported category: {category}")
    return DEFAULT_SCHEMAS[category]


def get_standard_fields(category: str) -> list[dict[str, Any]]:
    return get_default_schema(category)["fields"]


def get_standard_field_labels(category: str) -> list[str]:
    return [str(field["label"]) for field in get_standard_fields(category)]


def _normalize_field_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _coerce_discovered_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"number", "numeric", "amount", "currency"}:
        return "Number"
    if normalized in {"percentage", "percent", "%", "ratio"}:
        return "Percentage"
    if normalized in {"date", "datetime"}:
        return "Date"
    return "Text"


async def discover_additional_fields(
    *,
    category: str,
    document_text: str,
    existing_fields: list[str],
) -> list[dict[str, str]]:
    if not document_text.strip() or not has_text_llm():
        return []

    existing_names = {_normalize_field_name(field) for field in existing_fields}
    prompt = (
        f"This is a {category.replace('_', ' ')} financial document.\n"
        "The following fields have already been extracted:\n"
        f"{json.dumps(existing_fields, ensure_ascii=True)}\n\n"
        "Scan the document and identify ANY additional financial data points, ratios, metrics, "
        "or information that could be useful for credit analysis but are NOT in the above list.\n\n"
        "Return JSON array:\n"
        "[{\n"
        '  "field_name": string,\n'
        '  "field_type": "Number"|"Text"|"Percentage"|"Date",\n'
        '  "value_found": string,\n'
        '  "reason": string\n'
        "}]\n\n"
        "Return maximum 10 additional fields.\n"
        "Only return fields that actually exist in the document.\n"
        "Do not hallucinate fields.\n\n"
        f"Document:\n{document_text[:24000]}"
    )
    payload = await asyncio.to_thread(generate_json, prompt)
    if not isinstance(payload, list):
        return []

    discovered: list[dict[str, str]] = []
    seen_names: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        field_name = str(item.get("field_name") or "").strip()
        value_found = str(item.get("value_found") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not field_name or not value_found:
            continue
        normalized_name = _normalize_field_name(field_name)
        if normalized_name in existing_names or normalized_name in seen_names:
            continue
        seen_names.add(normalized_name)
        discovered.append(
            {
                "field_name": field_name,
                "field_type": _coerce_discovered_type(item.get("field_type")),
                "value_found": value_found,
                "reason": reason,
            }
        )
        if len(discovered) >= 10:
            break
    return discovered


async def get_case_schemas(session: AsyncSession, case_id: str) -> list[ExtractionSchema]:
    result = await session.execute(
        select(ExtractionSchema).where(ExtractionSchema.case_id == case_id).order_by(ExtractionSchema.document_category)
    )
    return list(result.scalars().all())


async def get_or_create_case_schema(session: AsyncSession, case_id: str, category: str) -> ExtractionSchema:
    result = await session.execute(
        select(ExtractionSchema)
        .where(ExtractionSchema.case_id == case_id, ExtractionSchema.document_category == category)
        .order_by(ExtractionSchema.schema_version.desc())
    )
    existing = result.scalars().first()
    if existing:
        return existing
    default = get_default_schema(category)
    schema = ExtractionSchema(
        case_id=case_id,
        document_category=category,
        schema_version=1,
        fields=default["fields"],
        is_default=True,
    )
    session.add(schema)
    await session.commit()
    await session.refresh(schema)
    return schema

