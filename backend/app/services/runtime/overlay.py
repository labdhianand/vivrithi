from __future__ import annotations

from pathlib import Path

import fitz

from .artifacts import ArtifactBBox, DocumentArtifact


def _denormalize_bbox(page: fitz.Page, bbox: ArtifactBBox | None) -> fitz.Rect | None:
    if bbox is None:
        return None
    width = float(page.rect.width or 1.0)
    height = float(page.rect.height or 1.0)
    return fitz.Rect(
        bbox.x1 * width,
        bbox.y1 * height,
        bbox.x2 * width,
        bbox.y2 * height,
    )


def render_overlay_pdf(pdf_path: Path, artifact: DocumentArtifact, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    blocks_by_page: dict[int, list] = {}
    tables_by_page: dict[int, list] = {}
    for block in artifact.text_blocks:
        blocks_by_page.setdefault(block.page_number, []).append(block)
    for table in artifact.tables:
        tables_by_page.setdefault(table.page_number, []).append(table)

    for page_number, page in enumerate(doc, start=1):
        for block in blocks_by_page.get(page_number, []):
            rect = _denormalize_bbox(page, block.bbox)
            if rect is not None:
                page.draw_rect(rect, color=(0.12, 0.63, 0.22), width=0.8)
        for table in tables_by_page.get(page_number, []):
            rect = _denormalize_bbox(page, table.bbox)
            if rect is not None:
                page.draw_rect(rect, color=(0.88, 0.49, 0.0), width=1.4)
    doc.save(out_path)
    doc.close()
    return out_path
