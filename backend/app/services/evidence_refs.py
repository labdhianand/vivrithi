from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from ..models.analyst_note import AnalystNote
from ..models.extraction import Extraction
from ..models.research import ResearchItem


EvidenceRef = dict[str, object]


def build_extraction_index(extractions: Iterable[Extraction]) -> dict[str, list[Extraction]]:
    index: dict[str, list[Extraction]] = defaultdict(list)
    for extraction in extractions:
        index[extraction.schema_field_key].append(extraction)
    return index


def extraction_ref(extraction: Extraction, *, label: str | None = None) -> EvidenceRef:
    document = extraction.document
    return {
        "kind": "extraction",
        "label": label or extraction.field_label or extraction.schema_field_key.replace("_", " "),
        "document_id": extraction.document_id,
        "document_name": document.original_filename if document else None,
        "document_category": document.user_category if document else None,
        "page_number": extraction.source_page_number,
        "extraction_id": extraction.id,
        "schema_field_key": extraction.schema_field_key,
    }


def first_extraction_ref(
    extraction_index: dict[str, list[Extraction]],
    key: str,
    *,
    label: str | None = None,
) -> EvidenceRef | None:
    items = extraction_index.get(key) or []
    for extraction in items:
        if extraction.value or extraction.user_edited_value or extraction.value_numeric is not None:
            return extraction_ref(extraction, label=label)
    if items:
        return extraction_ref(items[0], label=label)
    return None


def refs_for_keys(
    extraction_index: dict[str, list[Extraction]],
    keys: Iterable[str],
) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    seen: set[tuple[str | None, str | None]] = set()
    for key in keys:
        ref = first_extraction_ref(extraction_index, key)
        if not ref:
            continue
        ref_key = (str(ref.get("document_id") or ""), str(ref.get("schema_field_key") or ""))
        if ref_key in seen:
            continue
        seen.add(ref_key)
        refs.append(ref)
    return refs


def research_ref(item: ResearchItem, *, label: str | None = None) -> EvidenceRef:
    return {
        "kind": "research",
        "label": label or item.title or item.source_name or "Research item",
        "research_id": item.id,
        "source_name": item.source_name,
        "url": item.source_url,
        "published_date": item.published_date.isoformat() if item.published_date else None,
        "category": item.category,
    }


def note_ref(note: AnalystNote, *, label: str | None = None) -> EvidenceRef:
    return {
        "kind": "analyst_note",
        "label": label or note.note_type or "Analyst note",
        "note_id": note.id,
        "affected_c": note.affected_c,
        "content": note.content[:180],
    }
