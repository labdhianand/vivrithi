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
    document = getattr(extraction, "document", None)
    return {
        "kind": "extraction",
        "label": label or getattr(extraction, "field_label", None) or extraction.schema_field_key.replace("_", " "),
        "document_id": getattr(extraction, "document_id", None),
        "document_name": getattr(document, "original_filename", None) if document else None,
        "document_category": getattr(document, "user_category", None) if document else None,
        "page_number": getattr(extraction, "source_page_number", None),
        "extraction_id": getattr(extraction, "id", None),
        "schema_field_key": getattr(extraction, "schema_field_key", None),
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
        "label": label or getattr(item, "title", None) or getattr(item, "source_name", None) or "Research item",
        "research_id": getattr(item, "id", None),
        "source_name": getattr(item, "source_name", None),
        "url": getattr(item, "source_url", None),
        "published_date": item.published_date.isoformat() if getattr(item, "published_date", None) else None,
        "category": getattr(item, "category", None),
        "verification_status": getattr(item, "verification_status", None),
        "entity_scope": getattr(item, "entity_scope", None),
    }


def note_ref(note: AnalystNote, *, label: str | None = None) -> EvidenceRef:
    return {
        "kind": "analyst_note",
        "label": label or getattr(note, "note_type", None) or "Analyst note",
        "note_id": getattr(note, "id", None),
        "affected_c": getattr(note, "affected_c", None),
        "content": getattr(note, "content", "")[:180],
    }
