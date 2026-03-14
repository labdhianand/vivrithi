from __future__ import annotations

import json
from pathlib import Path

import fitz

from ..config import get_settings
from .gemini import generate_from_file
from .types import ParsedPage


def _parse_payload(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"markdown": text, "text": text, "bounding_boxes": []}


async def parse_page_gemini_vision(pdf_path: Path, page_num: int, page_image_path: Path) -> ParsedPage:
    settings = get_settings()
    if not settings.gemini_api_key:
        with fitz.open(pdf_path) as doc:
            text = doc[page_num].get_text("text")
        return ParsedPage(
            page_number=page_num + 1,
            text=text,
            markdown=text,
            bounding_boxes=[],
            parser_used="gemini_vision_fallback",
            confidence=0.45 if text.strip() else 0.2,
        )

    prompt = (
        "Extract all visible text and tables from this page. "
        "Return JSON with keys text, markdown, and bounding_boxes."
    )
    payload = _parse_payload(
        generate_from_file(
            prompt,
            page_image_path,
            model=settings.gemini_vision_model,
            response_mime_type="application/json",
        )
        or ""
    )
    return ParsedPage(
        page_number=page_num + 1,
        text=payload.get("text", ""),
        markdown=payload.get("markdown", payload.get("text", "")),
        tables=[],
        bounding_boxes=payload.get("bounding_boxes", []),
        parser_used="gemini_vision",
        confidence=0.78,
    )
