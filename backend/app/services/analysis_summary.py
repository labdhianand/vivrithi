from __future__ import annotations

import json
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.analyst_note import AnalystNote
from ..models.case import Case, CrossVerification
from ..models.document import Document
from ..models.extraction import Extraction
from ..models.research import ResearchItem
from ..models.schema import ExtractionSchema


def _doc_category(document: Document) -> str:
    return document.user_category or document.auto_category or "Unclassified"


def _display_value(extraction: Extraction) -> str:
    if extraction.user_edited_value:
        return extraction.user_edited_value
    if extraction.value:
        return extraction.value
    if extraction.value_numeric is not None:
        return str(extraction.value_numeric)
    return ""


async def build_case_analysis_summary(session: AsyncSession, case_id: str) -> dict:
    case = await session.get(Case, case_id)
    if not case:
        raise ValueError("Case not found")

    documents = list(
        (
            await session.execute(
                select(Document).where(Document.case_id == case_id).order_by(Document.created_at.desc())
            )
        ).scalars().all()
    )
    extractions = list(
        (
            await session.execute(
                select(Extraction)
                .join(Document, Document.id == Extraction.document_id)
                .where(Document.case_id == case_id)
                .options(selectinload(Extraction.document))
            )
        ).scalars().all()
    )
    schemas = list(
        (
            await session.execute(
                select(ExtractionSchema).where(
                    (ExtractionSchema.case_id == case_id) | (ExtractionSchema.case_id.is_(None))
                )
            )
        ).scalars().all()
    )
    research_items = list(
        (await session.execute(select(ResearchItem).where(ResearchItem.case_id == case_id))).scalars().all()
    )
    cross_checks = list(
        (
            await session.execute(
                select(CrossVerification).where(CrossVerification.case_id == case_id).order_by(CrossVerification.created_at.desc())
            )
        ).scalars().all()
    )
    notes = list(
        (
            await session.execute(
                select(AnalystNote).where(AnalystNote.case_id == case_id).order_by(AnalystNote.created_at.desc())
            )
        ).scalars().all()
    )

    latest_doc_by_category: dict[str, Document] = {}
    for document in documents:
        category = _doc_category(document)
        latest_doc_by_category.setdefault(category, document)

    schema_by_category: dict[str, ExtractionSchema] = {}
    ordered_schemas = sorted(
        schemas,
        key=lambda item: (
            1 if item.case_id == case_id else 0,
            item.schema_version,
            1 if item.is_default else 0,
        ),
        reverse=True,
    )
    for schema in ordered_schemas:
        schema_by_category.setdefault(schema.document_category, schema)

    extractions_by_doc: dict[str, dict[str, Extraction]] = defaultdict(dict)
    for extraction in extractions:
        extractions_by_doc[extraction.document_id][extraction.schema_field_key] = extraction

    missing_required_fields: list[dict] = []
    for category, schema in schema_by_category.items():
        document = latest_doc_by_category.get(category)
        extraction_map = extractions_by_doc.get(document.id, {}) if document else {}
        for field in schema.fields:
            if not field.get("required"):
                continue
            extraction = extraction_map.get(field["key"])
            if extraction and _display_value(extraction).strip():
                continue
            missing_required_fields.append(
                {
                    "document_category": category,
                    "field_key": field["key"],
                    "field_label": field.get("label") or field["key"].replace("_", " "),
                    "document_id": document.id if document else None,
                    "document_name": document.original_filename if document else None,
                }
            )

    contradictions = [
        {
            "id": check.id,
            "check_name": check.check_name,
            "status": check.status,
            "doc_a": check.doc_a,
            "doc_b": check.doc_b,
            "note": check.note,
            "value_a": check.value_a,
            "value_b": check.value_b,
        }
        for check in cross_checks
        if check.status == "mismatch"
    ]

    research_counts_by_status: dict[str, int] = defaultdict(int)
    research_counts_by_scope: dict[str, int] = defaultdict(int)
    verified_research_items: list[dict] = []
    contextual_research_items: list[dict] = []
    for item in research_items:
        status = item.verification_status or "unknown"
        scope = item.entity_scope or "generic"
        research_counts_by_status[status] += 1
        research_counts_by_scope[scope] += 1
        payload = {
            "id": item.id,
            "category": item.category,
            "title": item.title,
            "severity": item.severity,
            "verification_status": item.verification_status,
            "entity_scope": item.entity_scope,
            "match_explanation": item.match_explanation,
            "matched_terms": item.matched_terms,
            "source_url": item.source_url,
        }
        if item.verification_status in {"verified", "probable"} and item.entity_scope in {"borrower", "promoter"}:
            verified_research_items.append(payload)
        elif item.verification_status in {"verified", "probable", "contextual"} and item.entity_scope in {"sector", "macro"}:
            contextual_research_items.append(payload)

    note_impacts = [
        {
            "id": note.id,
            "note_type": note.note_type,
            "affected_c": note.affected_c,
            "sentiment": note.sentiment,
            "risk_adjustment": note.risk_adjustment,
            "content": note.content,
        }
        for note in notes
    ]

    return {
        "case_id": case_id,
        "missing_required_fields": missing_required_fields,
        "contradictions": contradictions,
        "research_digest": {
            "counts_by_status": dict(research_counts_by_status),
            "counts_by_scope": dict(research_counts_by_scope),
            "verified_borrower_items": verified_research_items[:6],
            "contextual_items": contextual_research_items[:6],
        },
        "note_impacts": note_impacts,
    }
