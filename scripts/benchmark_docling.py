"""Benchmark stock Docling vs FastFork on OneDrive PDFs."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "docling_fastfork"))

ONEDRIVE = ROOT / "OneDrive_1_14-3-2026"
OUTPUT_DIR = ROOT / "data" / "benchmarks" / "docling_benchmark"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_pdfs() -> list[dict]:
    pdfs = []
    for pdf_path in sorted(ONEDRIVE.rglob("*.pdf")):
        rel = str(pdf_path.relative_to(ONEDRIVE))
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        file_size = pdf_path.stat().st_size
        doc.close()
        pdfs.append({
            "path": str(pdf_path),
            "rel_path": rel,
            "page_count": page_count,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
        })
    return pdfs


def run_stock_docling(pdf_path: str) -> dict:
    """Run stock Docling DocumentConverter."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    t0 = time.time()
    result = converter.convert(pdf_path)
    elapsed = time.time() - t0

    document = result.document
    markdown = document.export_to_markdown()
    text = document.export_to_text()
    page_count = len(document.pages)
    tables = [item for item in document.iterate_items() if hasattr(item, 'data') and hasattr(item.data, 'table_cells')]

    return {
        "status": "ok",
        "time_s": round(elapsed, 2),
        "markdown_length": len(markdown),
        "text_length": len(text),
        "pages_returned": page_count,
        "markdown": markdown,
    }


def run_fastfork(pdf_path: str) -> dict:
    """Run FastFork converter."""
    from docling.experimental.fastfork import FastForkDocumentConverter

    converter = FastForkDocumentConverter(max_workers=8, fallback_to_docling_for_scans=True)
    t0 = time.time()
    run = converter.convert(Path(pdf_path))
    elapsed = time.time() - t0

    artifact = run.fast_artifact
    return {
        "status": "ok",
        "time_s": round(elapsed, 2),
        "markdown_length": len(artifact.markdown),
        "text_length": len(artifact.text),
        "pages_returned": artifact.page_count,
        "tables_found": len(artifact.tables),
        "used_docling_fallback": run.used_docling_fallback,
        "fallback_pages": run.fallback_page_numbers,
        "timings": run.timings,
        "markdown": artifact.markdown,
    }


def benchmark_one(pdf_info: dict) -> dict:
    rel = pdf_info["rel_path"]
    path = pdf_info["path"]
    pages = pdf_info["page_count"]
    size_mb = pdf_info["file_size_mb"]

    print(f"\n{'─'*70}")
    print(f"  {rel}  ({pages} pages, {size_mb} MB)")
    print(f"{'─'*70}")

    result = {"document": rel, "pages": pages, "size_mb": size_mb}
    safe_name = rel.replace("/", "_").replace(" ", "_").replace(".pdf", "")

    # ── FastFork ──
    print(f"  FastFork    ... ", end="", flush=True)
    try:
        ff = run_fastfork(path)
        print(f"OK  {ff['time_s']:.1f}s  {ff['markdown_length']} chars  "
              f"tables={ff['tables_found']}  fallback={ff['used_docling_fallback']}")
        result["fastfork"] = {k: v for k, v in ff.items() if k != "markdown"}
        with open(OUTPUT_DIR / f"{safe_name}_fastfork.md", "w") as f:
            f.write(ff["markdown"])
    except Exception as e:
        print(f"FAIL  {str(e)[:100]}")
        result["fastfork"] = {"status": "error", "error": str(e)[:200]}

    # ── Stock Docling ──
    print(f"  Stock       ... ", end="", flush=True)
    try:
        sd = run_stock_docling(path)
        print(f"OK  {sd['time_s']:.1f}s  {sd['markdown_length']} chars  "
              f"pages={sd['pages_returned']}")
        result["stock"] = {k: v for k, v in sd.items() if k != "markdown"}
        with open(OUTPUT_DIR / f"{safe_name}_stock.md", "w") as f:
            f.write(sd["markdown"])
    except Exception as e:
        print(f"FAIL  {str(e)[:100]}")
        result["stock"] = {"status": "error", "error": str(e)[:200]}

    return result


def main():
    pdfs = get_all_pdfs()
    total_pages = sum(p["page_count"] for p in pdfs)

    print(f"Docling Benchmark: Stock vs FastFork")
    print(f"PDFs: {len(pdfs)} files, {total_pages} total pages\n")
    for i, p in enumerate(pdfs, 1):
        print(f"  {i:2d}. {p['rel_path']} ({p['page_count']} pg, {p['file_size_mb']} MB)")

    all_results = []
    grand_start = time.time()

    for pdf_info in pdfs:
        r = benchmark_one(pdf_info)
        all_results.append(r)

    grand_total = time.time() - grand_start

    # ── Final Report ──
    print(f"\n{'='*70}")
    print(f"  DOCLING BENCHMARK: Stock vs FastFork")
    print(f"{'='*70}\n")
    print(f"  Total wall time: {grand_total:.1f}s ({grand_total/60:.1f} min)\n")

    hdr = f"  {'Document':<40} {'Pgs':>4} {'FF-Time':>8} {'FF-Chars':>9} {'SD-Time':>8} {'SD-Chars':>9} {'Speedup':>8}"
    print(hdr)
    print(f"  {'-'*40} {'-'*4} {'-'*8} {'-'*9} {'-'*8} {'-'*9} {'-'*8}")

    for r in all_results:
        ff = r.get("fastfork", {})
        sd = r.get("stock", {})
        ff_t = f"{ff.get('time_s', 0):.1f}s" if ff.get("status") == "ok" else "FAIL"
        ff_c = f"{ff.get('markdown_length', 0):,}" if ff.get("status") == "ok" else "-"
        sd_t = f"{sd.get('time_s', 0):.1f}s" if sd.get("status") == "ok" else "FAIL"
        sd_c = f"{sd.get('markdown_length', 0):,}" if sd.get("status") == "ok" else "-"
        if ff.get("status") == "ok" and sd.get("status") == "ok" and ff["time_s"] > 0:
            speedup = f"{sd['time_s'] / ff['time_s']:.1f}x"
        else:
            speedup = "-"
        print(f"  {r['document']:<40} {r['pages']:>4} {ff_t:>8} {ff_c:>9} {sd_t:>8} {sd_c:>9} {speedup:>8}")

    # Save
    output_file = OUTPUT_DIR / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "grand_total_time_s": round(grand_total, 2),
            "total_pages": total_pages,
            "documents": all_results,
        }, f, indent=2)
    print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    main()
