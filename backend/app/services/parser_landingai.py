from __future__ import annotations

from pathlib import Path

import httpx

from ..config import get_settings
from .parser_pdfplumber import parse_page_pdfplumber
from .parser_vision import parse_page_gemini_vision
from .types import ParsedPage, ParsedTable


LANDING_AI_URL = "https://api.landing.ai/v1/tools/agentic-document-analysis"


async def parse_page_landingai(pdf_path: Path, page_num: int, page_image_path: Path) -> ParsedPage:
    settings = get_settings()
    if not settings.landing_ai_api_key:
        if settings.gemini_api_key:
            page = await parse_page_gemini_vision(pdf_path, page_num, page_image_path)
            page.parser_used = "landingai_gemini_fallback"
            page.confidence = max(page.confidence, 0.7)
            return page
        page = parse_page_pdfplumber(pdf_path, page_num)
        page.parser_used = "landingai_fallback"
        page.confidence = min(page.confidence, 0.65)
        return page

    with page_image_path.open("rb") as handle:
        files = {"image": handle}
        data = {
            "prompt": (
                "Extract all text and tables from this financial document page. "
                "Return JSON with text, markdown, tables, and bounding_boxes."
            )
        }
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                LANDING_AI_URL,
                headers={"Authorization": f"Bearer {settings.landing_ai_api_key}"},
                files=files,
                data=data,
            )
        response.raise_for_status()
        payload = response.json()

    tables: list[ParsedTable] = []
    for raw_table in payload.get("tables", []):
        tables.append(
            ParsedTable(
                bbox=tuple(raw_table.get("bbox", [0.0, 0.0, 1.0, 1.0])),
                rows=raw_table.get("rows", []),
                markdown=raw_table.get("markdown", ""),
            )
        )
    return ParsedPage(
        page_number=page_num + 1,
        text=payload.get("text", ""),
        markdown=payload.get("markdown", payload.get("text", "")),
        tables=tables,
        bounding_boxes=payload.get("bounding_boxes", []),
        parser_used="landingai",
        confidence=0.9,
    )
