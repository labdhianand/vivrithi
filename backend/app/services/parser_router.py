from __future__ import annotations

from .types import PageTriageResult


def route_page(triage: PageTriageResult) -> str:
    if triage.content_type in {"blank", "signature_page"}:
        return "skip"
    if triage.has_tables:
        return "landingai" if triage.is_scanned else "pdfplumber"
    if triage.is_scanned:
        return "gemini_vision"
    return "pdfplumber"
