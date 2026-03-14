from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
from time import perf_counter

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.runtime.pipeline import FastDocumentPipeline


def _field_has_value(item) -> bool:
    return item.value not in (None, "", "[]")


async def run_benchmark(pdf_path: Path, forced_category: str | None, max_workers: int) -> dict:
    started = perf_counter()
    pipeline = FastDocumentPipeline(max_workers=max_workers)
    result = await pipeline.run(pdf_path, forced_category=forced_category)
    active_values = result.active_values()
    missing_fields = [
        item.key
        for item in result.extraction.extraction_results
        if not _field_has_value(item)
    ]
    return {
        "pdf_path": str(pdf_path),
        "forced_category": forced_category,
        "page_count": result.document.page_count,
        "classification": {
            "category": result.classification_category,
            "confidence": result.classification_confidence,
        },
        "document": {
            "parse_seconds": round(result.document.parse_seconds, 6),
            "route_counts": result.document.route_counts,
            "content_type_counts": result.document.content_type_counts,
        },
        "extraction": {
            "schema_category": result.extraction.schema_category,
            "extraction_seconds": round(result.extraction.extraction_seconds, 6),
            "field_fill_count": result.extraction.field_fill_count,
            "candidate_pages": [page.page_number for page in result.extraction.candidate_pages],
            "active_values": active_values,
            "missing_fields": missing_fields,
        },
        "total_seconds": round(perf_counter() - started, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark annual report parsing and extraction.")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("data/challenge_doc_corpus/raw/Annual_Report/mid/Aavas_Financiers/Annual_Report_FY2024-25.pdf"),
    )
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/benchmarks/annual_report_benchmark_aavas.json"),
    )
    args = parser.parse_args()

    payload = asyncio.run(run_benchmark(args.pdf.resolve(), args.category, args.max_workers))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    main()
