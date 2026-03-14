"""Benchmark Landing AI document analysis on all claude_data PDFs."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import fitz
import httpx

ROOT = Path(__file__).resolve().parents[1]

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("LANDINGAI_API_KEY")
ENDPOINT = os.getenv("LANDINGAI_ENDPOINT", "https://api.va.landing.ai/v1")
# New recommended parse endpoint
PARSE_URL = f"{ENDPOINT}/ade/parse"

CLAUDE_DATA = ROOT / "claude_data"
OUTPUT_DIR = ROOT / "data" / "benchmarks" / "landingai_benchmark"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_pdfs() -> list[dict]:
    pdfs = []
    for pdf_path in sorted(CLAUDE_DATA.rglob("*.pdf")):
        rel = pdf_path.relative_to(CLAUDE_DATA)
        parts = rel.parts
        company = parts[0] if len(parts) > 1 else "unknown"
        doc_type = parts[1] if len(parts) > 2 else "unknown"
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        file_size = pdf_path.stat().st_size
        doc.close()
        pdfs.append({
            "path": str(pdf_path),
            "rel_path": str(rel),
            "company": company,
            "doc_type": doc_type,
            "page_count": page_count,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
        })
    return pdfs


async def call_landingai_parse(pdf_path: Path, client: httpx.AsyncClient) -> dict:
    """Send PDF directly to Landing AI new Parse API."""
    with open(pdf_path, "rb") as f:
        files = {"document": (pdf_path.name, f, "application/pdf")}
        data = {"model": "dpt-2-latest", "split": "page"}
        response = await client.post(
            PARSE_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files=files,
            data=data,
        )
    if response.status_code != 200:
        print(f"\n    Response {response.status_code}: {response.text[:300]}")
    response.raise_for_status()
    return response.json()


async def benchmark_document(pdf_info: dict) -> dict:
    pdf_path = pdf_info["path"]
    page_count = pdf_info["page_count"]
    rel_path = pdf_info["rel_path"]

    print(f"\n{'='*70}")
    print(f"  {rel_path}")
    print(f"  Pages: {page_count} | Size: {pdf_info['file_size_mb']} MB")
    print(f"{'='*70}")

    api_start = time.time()
    try:
        async with httpx.AsyncClient(timeout=480) as client:
            result = await call_landingai_parse(Path(pdf_path), client)
        api_time = time.time() - api_start

        # New parse API response structure
        markdown = result.get("markdown", "")
        chunks = result.get("chunks", [])
        splits = result.get("splits", [])
        metadata = result.get("metadata", {})

        text_len = len(markdown)
        table_count = sum(1 for c in chunks if c.get("type") == "table")
        chunk_count = len(chunks)
        duration_ms = metadata.get("duration_ms", 0)
        credit_usage = metadata.get("credit_usage", 0)

        status = "ok"
        error = None

        print(f"  OK  api={api_time:.1f}s  server={duration_ms}ms  "
              f"text={text_len} chars  chunks={chunk_count}  tables={table_count}  "
              f"credits={credit_usage}")

        # Save raw response
        resp_file = OUTPUT_DIR / rel_path.replace("/", "_").replace(".pdf", "_response.json")
        with open(resp_file, "w") as f:
            json.dump(result, f, indent=2, default=str)

    except Exception as e:
        api_time = time.time() - api_start
        text_len = 0
        table_count = 0
        chunk_count = 0
        duration_ms = 0
        credit_usage = 0
        status = "error"
        error = str(e)
        print(f"  FAIL  time={api_time:.1f}s  err={error[:120]}")

    return {
        "document": rel_path,
        "company": pdf_info["company"],
        "doc_type": pdf_info["doc_type"],
        "file_size_mb": pdf_info["file_size_mb"],
        "total_pages": page_count,
        "api_time_s": round(api_time, 2),
        "server_duration_ms": duration_ms,
        "time_per_page_s": round(api_time / max(page_count, 1), 2),
        "text_length": text_len,
        "chunk_count": chunk_count,
        "table_count": table_count,
        "credit_usage": credit_usage,
        "status": status,
        "error": error,
    }


async def main():
    if not API_KEY:
        print("ERROR: LANDINGAI_API_KEY not set in .env")
        sys.exit(1)

    print(f"Landing AI Parse API: {PARSE_URL}")
    print(f"API Key: {API_KEY[:12]}...")

    pdfs = get_all_pdfs()
    print(f"\nFound {len(pdfs)} documents:\n")
    for i, p in enumerate(pdfs, 1):
        print(f"  {i:2d}. {p['rel_path']} ({p['page_count']} pages, {p['file_size_mb']} MB)")

    total_pages = sum(p["page_count"] for p in pdfs)
    print(f"\n  Total: {total_pages} pages across {len(pdfs)} documents\n")

    all_results = []
    grand_start = time.time()

    for pdf_info in pdfs:
        result = await benchmark_document(pdf_info)
        all_results.append(result)

    grand_total = time.time() - grand_start

    ok_results = [r for r in all_results if r["status"] == "ok"]
    fail_results = [r for r in all_results if r["status"] == "error"]

    print(f"\n{'='*70}")
    print(f"  FINAL BENCHMARK REPORT")
    print(f"{'='*70}\n")

    print(f"  Total wall time:   {grand_total:.1f}s ({grand_total/60:.1f} min)")
    print(f"  Documents:         {len(ok_results)}/{len(all_results)} OK ({len(fail_results)} failed)")
    print(f"  Total pages:       {total_pages}")
    print(f"  Total text:        {sum(r['text_length'] for r in ok_results):,} chars")
    print(f"  Total tables:      {sum(r['table_count'] for r in ok_results)}")
    print(f"  Total credits:     {sum(r['credit_usage'] for r in ok_results)}")
    print()

    hdr = f"  {'Document':<55} {'Pgs':>4} {'Size':>6} {'Time':>7} {'T/pg':>6} {'Text':>9} {'Tbls':>5} {'Cred':>5} {'OK':>3}"
    print(hdr)
    print(f"  {'-'*55} {'-'*4} {'-'*6} {'-'*7} {'-'*6} {'-'*9} {'-'*5} {'-'*5} {'-'*3}")
    for r in all_results:
        ok = "Y" if r["status"] == "ok" else "N"
        print(f"  {r['document']:<55} {r['total_pages']:>4} {r['file_size_mb']:>5.1f}M "
              f"{r['api_time_s']:>6.1f}s {r['time_per_page_s']:>5.1f}s "
              f"{r['text_length']:>9,} {r['table_count']:>5} {r['credit_usage']:>5} {ok:>3}")

    if fail_results:
        print(f"\n  Failures:")
        for r in fail_results:
            print(f"    {r['document']}: {r['error'][:100]}")

    # Save results
    output_file = OUTPUT_DIR / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint": PARSE_URL,
            "model": "dpt-2-latest",
            "grand_total_time_s": round(grand_total, 2),
            "total_pages": total_pages,
            "documents_ok": len(ok_results),
            "documents_failed": len(fail_results),
            "total_text_chars": sum(r["text_length"] for r in ok_results),
            "total_tables": sum(r["table_count"] for r in ok_results),
            "total_credits": sum(r["credit_usage"] for r in ok_results),
            "documents": all_results,
        }, f, indent=2)
    print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
