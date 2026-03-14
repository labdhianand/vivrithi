#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the fast runtime against Docling.")
    parser.add_argument(
        "--company",
        choices=["aavas", "home", "all"],
        default="aavas",
        help="Which sample corpus to benchmark.",
    )
    parser.add_argument(
        "--include-annual-report",
        action="store_true",
        help="Include annual reports in the benchmark set.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Max workers for the fast runtime.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="JSON output path. Defaults to a company-specific file under data/benchmarks/.",
    )
    return parser.parse_args()


SAMPLE_DOCS = {
    "aavas": [
        {
            "category": "ALM",
            "path": ROOT_DIR / "claude_data" / "Aavas_Financiers" / "ALM" / "Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf",
            "expected": {
                "lcr_ratio": "151.7%",
                "hqla_total_weighted": "23,203",
                "total_net_cash_outflows": "15,291",
            },
        },
        {
            "category": "Borrowing_Profile",
            "path": ROOT_DIR / "claude_data" / "Aavas_Financiers" / "Borrowing_Profile" / "Credit_Rating_Reaffirmation_CARE_2024-12-13.pdf",
            "expected": {
                "rating_agency": "CARE Ratings Limited",
                "long_term_rating": "CARE AA",
                "long_term_outlook": "Stable",
                "rating_action": "Reaffirmed",
                "total_rated_facilities_crore": "9662.00",
            },
        },
        {
            "category": "Shareholding_Pattern",
            "path": ROOT_DIR / "claude_data" / "Aavas_Financiers" / "Shareholding_Pattern" / "Shareholding_Pattern_Q3_FY26.pdf",
            "expected": {
                "promoter_holding_percent": "48.95%",
                "public_holding_percent": "51.05%",
                "fpi_holding_percent": "24.72%",
                "promoter_name": "Aquilo House Pte. Ltd",
            },
        },
        {
            "category": "Portfolio_Performance",
            "path": ROOT_DIR / "claude_data" / "Aavas_Financiers" / "Portfolio_Cuts_Performance" / "Financial_Result_Q3_FY26.pdf",
            "expected": {},
        },
        {
            "category": "Annual_Report",
            "path": ROOT_DIR / "claude_data" / "Aavas_Financiers" / "Annual_Report" / "Annual_Report_FY2024-25.pdf",
            "expected": {},
        },
    ],
    "home": [
        {
            "category": "ALM",
            "path": ROOT_DIR / "claude_data" / "Home_First_Finance" / "ALM" / "LCR_disclosure_Dec_25.pdf",
            "expected": {},
        },
        {
            "category": "Borrowing_Profile",
            "path": ROOT_DIR / "claude_data" / "Home_First_Finance" / "Borrowing_Profile" / "Revision_in_Credit_Rating_CARE_2025-06-10.pdf",
            "expected": {},
        },
        {
            "category": "Shareholding_Pattern",
            "path": ROOT_DIR / "claude_data" / "Home_First_Finance" / "Shareholding_Pattern" / "Shareholding_Pattern_Q3_FY26.pdf",
            "expected": {},
        },
        {
            "category": "Portfolio_Performance",
            "path": ROOT_DIR / "claude_data" / "Home_First_Finance" / "Portfolio_Cuts_Performance" / "HomeFirst_Q3FY26_Financials.pdf",
            "expected": {},
        },
        {
            "category": "Annual_Report",
            "path": ROOT_DIR / "claude_data" / "Home_First_Finance" / "Annual_Report" / "Integrated_Annual_Report_FY25.pdf",
            "expected": {},
        },
    ],
}


@dataclass
class BenchmarkRow:
    document: str
    category: str
    fast_seconds: float
    fast_parse_seconds: float
    fast_extract_seconds: float
    fast_page_count: int
    fast_candidate_page_count: int
    fast_field_fill_count: int
    fast_expected_hits: int
    fast_expected_total: int
    docling_seconds: float | None
    docling_page_count: int | None
    docling_expected_hits: int
    docling_markdown_chars: int | None
    faster_backend: str


def pick_documents(company: str, include_annual_report: bool) -> list[dict]:
    if company == "all":
        documents = SAMPLE_DOCS["aavas"] + SAMPLE_DOCS["home"]
    else:
        documents = SAMPLE_DOCS[company]
    if include_annual_report:
        return documents
    return [item for item in documents if item["category"] != "Annual_Report"]


def count_docling_hits(expected: dict[str, str], markdown: str, text: str) -> int:
    haystack = f"{markdown}\n{text}"
    return sum(1 for value in expected.values() if value in haystack)


def normalize_value(value: str | None) -> str:
    return (value or "").strip().rstrip(".")


async def run_fast_benchmark(pipeline, pdf_path: Path, category: str):
    started = perf_counter()
    result = await pipeline.run(pdf_path, forced_category=category)
    elapsed = perf_counter() - started
    return elapsed, result


def main() -> int:
    args = parse_args()
    os.environ["GEMINI_API_KEY"] = ""

    from backend.app.config import get_settings
    from backend.app.services.runtime import DoclingBackend, FastDocumentPipeline

    get_settings.cache_clear()

    documents = pick_documents(args.company, include_annual_report=args.include_annual_report)
    pipeline = FastDocumentPipeline(max_workers=args.workers)
    docling = DoclingBackend()
    rows: list[BenchmarkRow] = []

    # Warm docling once so the comparison is closer to steady-state throughput.
    warmup_doc = documents[0]["path"]
    warmup_result = docling.convert(warmup_doc)
    print(
        f"docling_warmup document={warmup_doc.name} seconds={warmup_result.convert_seconds:.3f} pages={warmup_result.page_count}"
    )

    for item in documents:
        fast_seconds, fast_result = asyncio.run(
            run_fast_benchmark(
                pipeline=pipeline,
                pdf_path=item["path"],
                category=item["category"],
            )
        )
        expected = item["expected"]
        fast_values = fast_result.active_values()
        fast_expected_hits = sum(
            1 for key, value in expected.items() if normalize_value(fast_values.get(key)) == normalize_value(value)
        )

        docling_seconds = None
        docling_page_count = None
        docling_markdown_chars = None
        docling_expected_hits = 0
        if item["category"] != "Annual_Report":
            docling_result = docling.convert(item["path"])
            docling_seconds = docling_result.convert_seconds
            docling_page_count = docling_result.page_count
            docling_markdown_chars = len(docling_result.markdown)
            docling_expected_hits = count_docling_hits(expected, docling_result.markdown, docling_result.text)

        faster_backend = "fast_runtime"
        if docling_seconds is not None and docling_seconds < fast_seconds:
            faster_backend = "docling"

        row = BenchmarkRow(
            document=item["path"].name,
            category=item["category"],
            fast_seconds=round(fast_seconds, 3),
            fast_parse_seconds=round(fast_result.document.parse_seconds, 3),
            fast_extract_seconds=round(fast_result.extraction.extraction_seconds, 3),
            fast_page_count=fast_result.document.page_count,
            fast_candidate_page_count=len(fast_result.extraction.candidate_pages),
            fast_field_fill_count=fast_result.extraction.field_fill_count,
            fast_expected_hits=fast_expected_hits,
            fast_expected_total=len(expected),
            docling_seconds=round(docling_seconds, 3) if docling_seconds is not None else None,
            docling_page_count=docling_page_count,
            docling_expected_hits=docling_expected_hits,
            docling_markdown_chars=docling_markdown_chars,
            faster_backend=faster_backend,
        )
        rows.append(row)
        print(
            f"{row.document} | fast={row.fast_seconds:.3f}s candidates={row.fast_candidate_page_count}/{row.fast_page_count} "
            f"fill={row.fast_field_fill_count} expected={row.fast_expected_hits}/{row.fast_expected_total} "
            f"| docling={row.docling_seconds if row.docling_seconds is not None else 'skipped'} "
            f"expected={row.docling_expected_hits}/{row.fast_expected_total} | winner={row.faster_backend}"
        )

    if args.output:
        output_path = Path(args.output)
    else:
        suffix = args.company
        if args.include_annual_report:
            suffix = f"{suffix}_with_annual"
        output_path = ROOT_DIR / "data" / "benchmarks" / f"fast_runtime_vs_docling_{suffix}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([asdict(row) for row in rows], indent=2), encoding="utf-8")
    print(f"saved_report={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
