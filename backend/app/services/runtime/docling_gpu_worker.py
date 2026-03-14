from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _norm_bbox(prov: dict | None, page_sizes: dict[int, tuple[float, float]]) -> list[float] | None:
    if not prov:
        return None
    bbox = prov.get("bbox") or {}
    page_number = int(prov.get("page_no") or 0)
    if page_number <= 0:
        return None
    page_size = page_sizes.get(page_number)
    if page_size is None:
        return None
    width, height = page_size
    if not width or not height:
        return None
    left = float(bbox.get("l", 0.0))
    right = float(bbox.get("r", 0.0))
    top = float(bbox.get("t", 0.0))
    bottom = float(bbox.get("b", 0.0))
    coord_origin = str(bbox.get("coord_origin", "TOPLEFT")).upper()
    if coord_origin == "BOTTOMLEFT":
        y1 = (height - top) / height
        y2 = (height - bottom) / height
    else:
        y1 = top / height
        y2 = bottom / height
    x1 = left / width
    x2 = right / width
    return [
        round(min(x1, x2), 6),
        round(min(y1, y2), 6),
        round(max(x1, x2), 6),
        round(max(y1, y2), 6),
    ]


def _table_rows(table_item: dict) -> list[list[str | None]]:
    data = table_item.get("data") or {}
    cells = data.get("table_cells") or []
    if not cells:
        return []
    max_row = 0
    max_col = 0
    for cell in cells:
        max_row = max(max_row, int(cell.get("end_row_offset_idx", 0)))
        max_col = max(max_col, int(cell.get("end_col_offset_idx", 0)))
    rows: list[list[str | None]] = [
        [None for _ in range(max_col + 1)]
        for _ in range(max_row + 1)
    ]
    for cell in cells:
        row_index = int(cell.get("start_row_offset_idx", 0))
        col_index = int(cell.get("start_col_offset_idx", 0))
        rows[row_index][col_index] = _clean_text(cell.get("text") or "")
    while rows and not any(_clean_text(value) for value in rows[-1]):
        rows.pop()
    return rows


def _table_markdown(rows: list[list[str | None]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [
        [(_clean_text(value) or "") for value in row] + [""] * (width - len(row))
        for row in rows
    ]
    header = normalized[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _build_pdf_converter(args):
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import RapidOcrOptions, ThreadedPdfPipelineOptions
    from docling.datamodel.settings import settings
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.threaded_standard_pdf_pipeline import ThreadedStandardPdfPipeline

    settings.perf.page_batch_size = args.page_batch_size

    pipeline_options = ThreadedPdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA),
        ocr_batch_size=args.ocr_batch_size,
        layout_batch_size=args.layout_batch_size,
        table_batch_size=args.table_batch_size,
    )
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = RapidOcrOptions(backend="torch")

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=ThreadedStandardPdfPipeline,
                pipeline_options=pipeline_options,
            )
        }
    )


def _build_default_converter():
    from docling.document_converter import DocumentConverter

    return DocumentConverter()


def convert_document(args) -> dict:
    input_path = Path(args.input_path)
    suffix = input_path.suffix.lower()
    started = time.perf_counter()
    if suffix == ".pdf":
        converter = _build_pdf_converter(args)
    else:
        converter = _build_default_converter()
    result = converter.convert(input_path)
    elapsed = time.perf_counter() - started
    document = result.document
    raw_dict = document.export_to_dict()
    markdown = document.export_to_markdown()
    text = document.export_to_text()

    page_sizes = {
        int(page_no): (
            float(payload["size"]["width"]),
            float(payload["size"]["height"]),
        )
        for page_no, payload in (raw_dict.get("pages") or {}).items()
    }
    pages = {
        page_number: {
            "page_number": page_number,
            "width": width,
            "height": height,
            "text_parts": [],
            "markdown_parts": [],
            "tables": [],
            "bounding_boxes": [],
        }
        for page_number, (width, height) in page_sizes.items()
    }

    text_blocks: list[dict] = []
    for index, item in enumerate(raw_dict.get("texts") or []):
        prov = (item.get("prov") or [{}])[0]
        page_number = int(prov.get("page_no") or 0)
        if page_number <= 0:
            continue
        bbox = _norm_bbox(prov, page_sizes)
        block_text = _clean_text(item.get("text") or item.get("orig") or "")
        text_blocks.append(
            {
                "block_id": item.get("self_ref", f"text-{index}"),
                "page_number": page_number,
                "label": str(item.get("label") or "text"),
                "text": block_text,
                "bbox": bbox,
                "reading_order_index": index,
                "source_engine": "docling_gpu",
            }
        )
        page_state = pages.setdefault(
            page_number,
            {
                "page_number": page_number,
                "width": page_sizes.get(page_number, (1.0, 1.0))[0],
                "height": page_sizes.get(page_number, (1.0, 1.0))[1],
                "text_parts": [],
                "markdown_parts": [],
                "tables": [],
                "bounding_boxes": [],
            },
        )
        if block_text:
            page_state["text_parts"].append(block_text)
            page_state["markdown_parts"].append(block_text)
            if bbox:
                page_state["bounding_boxes"].append({"text": block_text, "bbox": bbox})

    artifact_tables: list[dict] = []
    for table_index, item in enumerate(raw_dict.get("tables") or []):
        prov = (item.get("prov") or [{}])[0]
        page_number = int(prov.get("page_no") or 0)
        rows = _table_rows(item)
        table_markdown = _table_markdown(rows)
        bbox = _norm_bbox(prov, page_sizes)
        table_cells = []
        for cell in (item.get("data") or {}).get("table_cells") or []:
            table_cells.append(
                {
                    "row_index": int(cell.get("start_row_offset_idx", 0)),
                    "column_index": int(cell.get("start_col_offset_idx", 0)),
                    "text": _clean_text(cell.get("text") or ""),
                    "bbox": None,
                }
            )
        table_payload = {
            "table_id": item.get("self_ref", f"table-{table_index}"),
            "page_number": page_number,
            "bbox": bbox,
            "markdown": table_markdown,
            "row_count": len(rows),
            "column_count": max((len(row) for row in rows), default=0),
            "rows": rows,
            "cells": table_cells,
            "source_engine": "docling_gpu",
        }
        artifact_tables.append(table_payload)
        page_state = pages.setdefault(
            page_number,
            {
                "page_number": page_number,
                "width": page_sizes.get(page_number, (1.0, 1.0))[0],
                "height": page_sizes.get(page_number, (1.0, 1.0))[1],
                "text_parts": [],
                "markdown_parts": [],
                "tables": [],
                "bounding_boxes": [],
            },
        )
        page_state["tables"].append(
            {
                "bbox": bbox,
                "rows": rows,
                "markdown": table_markdown,
            }
        )
        if table_markdown:
            page_state["markdown_parts"].append(table_markdown)
            page_state["bounding_boxes"].append({"text": table_markdown, "bbox": bbox})

    serialized_pages = []
    for page_number in sorted(pages):
        page = pages[page_number]
        serialized_pages.append(
            {
                "page_number": page_number,
                "width": page["width"],
                "height": page["height"],
                "has_tables": bool(page["tables"]),
                "text": "\n".join(part for part in page["text_parts"] if part).strip(),
                "markdown": "\n\n".join(part for part in page["markdown_parts"] if part).strip(),
                "tables": page["tables"],
                "bounding_boxes": [item for item in page["bounding_boxes"] if item.get("bbox")],
            }
        )

    return {
        "backend": "docling_gpu_remote",
        "document_name": input_path.name,
        "source_path": str(input_path),
        "page_count": len(serialized_pages),
        "convert_seconds": round(elapsed, 6),
        "markdown": markdown,
        "text": text,
        "pages": serialized_pages,
        "text_blocks": text_blocks,
        "tables": artifact_tables,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Docling conversion on a remote GPU host.")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--page-batch-size", type=int, default=64)
    parser.add_argument("--layout-batch-size", type=int, default=64)
    parser.add_argument("--ocr-batch-size", type=int, default=64)
    parser.add_argument("--table-batch-size", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = convert_document(args)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
