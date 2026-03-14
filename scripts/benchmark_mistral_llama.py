"""Benchmark Mistral OCR vs LlamaParse on OneDrive PDFs."""
from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path

import fitz
import httpx

ROOT = Path(__file__).resolve().parents[1]
ONEDRIVE = ROOT / "OneDrive_1_14-3-2026"
OUTPUT_DIR = ROOT / "data" / "benchmarks" / "mistral_vs_llama"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MISTRAL_KEY = "ZOiWgNDeyC1zFTiRrrtkk4dffN9kE29S"
LLAMA_KEY = "llx-ZAX6zLR2UPa7CUmz7EamM6xyFj4AsDZjynd712KrdSvUTQ7S"

MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"
LLAMA_BASE_URL = "https://api.cloud.llamaindex.ai"


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


# ─── Mistral OCR ─────────────────────────────────────────────────────────────

async def parse_mistral(pdf_path: str, client: httpx.AsyncClient) -> dict:
    """Parse PDF via Mistral OCR API using base64 upload."""
    with open(pdf_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64}",
        },
        "include_image_base64": False,
    }
    resp = await client.post(
        MISTRAL_OCR_URL,
        headers={
            "Authorization": f"Bearer {MISTRAL_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    if resp.status_code != 200:
        print(f"\n    Mistral {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()
    return resp.json()


# ─── LlamaParse ──────────────────────────────────────────────────────────────

async def parse_llama(pdf_path: str, client: httpx.AsyncClient) -> dict:
    """Parse PDF via LlamaParse v2 API — upload + poll."""
    headers = {"Authorization": f"Bearer {LLAMA_KEY}"}

    config = json.dumps({"tier": "cost_effective", "version": "latest"})

    with open(pdf_path, "rb") as f:
        resp = await client.post(
            f"{LLAMA_BASE_URL}/api/v2/parse/upload",
            headers=headers,
            files={"file": (Path(pdf_path).name, f, "application/pdf")},
            data={"configuration": config},
        )
    if resp.status_code != 200:
        print(f"\n    LlamaParse upload {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()
    upload_data = resp.json()
    job_id = upload_data.get("id") or upload_data["job"]["id"]

    # Poll for completion
    while True:
        status_resp = await client.get(
            f"{LLAMA_BASE_URL}/api/v2/parse/{job_id}",
            headers=headers,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["job"]["status"]
        if status == "COMPLETED":
            break
        elif status in ("FAILED", "CANCELED"):
            raise RuntimeError(f"LlamaParse job {status}: {status_resp.text[:200]}")
        await asyncio.sleep(2)

    # Fetch results
    result_resp = await client.get(
        f"{LLAMA_BASE_URL}/api/v2/parse/{job_id}",
        headers=headers,
        params={"expand": "markdown,text"},
    )
    result_resp.raise_for_status()
    return result_resp.json()


# ─── Benchmark runner ────────────────────────────────────────────────────────

async def benchmark_one(pdf_info: dict) -> dict:
    rel = pdf_info["rel_path"]
    path = pdf_info["path"]
    pages = pdf_info["page_count"]
    size_mb = pdf_info["file_size_mb"]

    print(f"\n{'─'*70}")
    print(f"  {rel}  ({pages} pages, {size_mb} MB)")
    print(f"{'─'*70}")

    result = {"document": rel, "pages": pages, "size_mb": size_mb}

    # ── Mistral ──
    print(f"  Mistral OCR ... ", end="", flush=True)
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            mresp = await parse_mistral(path, client)
        mt = time.time() - t0
        m_pages = mresp.get("pages", [])
        m_text = "\n\n".join(p.get("markdown", "") for p in m_pages)
        m_page_count = len(m_pages)
        print(f"OK  {mt:.1f}s  {len(m_text)} chars  {m_page_count} pages returned")
        result["mistral"] = {
            "status": "ok", "time_s": round(mt, 2),
            "time_per_page_s": round(mt / max(pages, 1), 2),
            "text_length": len(m_text), "pages_returned": m_page_count,
        }
        # Save response
        safe_name = rel.replace("/", "_").replace(" ", "_").replace(".pdf", "")
        with open(OUTPUT_DIR / f"{safe_name}_mistral.json", "w") as f:
            json.dump(mresp, f, indent=2, default=str)
    except Exception as e:
        mt = time.time() - t0
        print(f"FAIL  {mt:.1f}s  {str(e)[:100]}")
        result["mistral"] = {"status": "error", "time_s": round(mt, 2), "error": str(e)[:200]}

    # ── LlamaParse ──
    print(f"  LlamaParse  ... ", end="", flush=True)
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            lresp = await parse_llama(path, client)
        lt = time.time() - t0
        l_md_pages = lresp.get("markdown", {}).get("pages", [])
        l_txt_pages = lresp.get("text", {}).get("pages", [])
        l_text = "\n\n".join(p.get("markdown", "") for p in l_md_pages)
        if not l_text:
            l_text = "\n\n".join(p.get("text", "") for p in l_txt_pages)
        l_page_count = len(l_md_pages) or len(l_txt_pages)
        print(f"OK  {lt:.1f}s  {len(l_text)} chars  {l_page_count} pages returned")
        result["llama"] = {
            "status": "ok", "time_s": round(lt, 2),
            "time_per_page_s": round(lt / max(pages, 1), 2),
            "text_length": len(l_text), "pages_returned": l_page_count,
        }
        with open(OUTPUT_DIR / f"{safe_name}_llama.json", "w") as f:
            json.dump(lresp, f, indent=2, default=str)
    except Exception as e:
        lt = time.time() - t0
        print(f"FAIL  {lt:.1f}s  {str(e)[:100]}")
        result["llama"] = {"status": "error", "time_s": round(lt, 2), "error": str(e)[:200]}

    return result


async def main():
    pdfs = get_all_pdfs()
    total_pages = sum(p["page_count"] for p in pdfs)

    print(f"OneDrive PDFs: {len(pdfs)} files, {total_pages} total pages\n")
    for i, p in enumerate(pdfs, 1):
        print(f"  {i:2d}. {p['rel_path']} ({p['page_count']} pg, {p['file_size_mb']} MB)")

    # Cost estimates
    print(f"\n  Estimated costs for {total_pages} pages:")
    print(f"    Mistral OCR:  {total_pages} pages × $0.001 = ${total_pages * 0.001:.2f}")
    print(f"    LlamaParse:   {total_pages} pages × 3 credits × $0.00125 = ${total_pages * 3 * 0.00125:.2f}")

    all_results = []
    grand_start = time.time()

    for pdf_info in pdfs:
        r = await benchmark_one(pdf_info)
        all_results.append(r)

    grand_total = time.time() - grand_start

    # ── Final Report ──
    print(f"\n{'='*70}")
    print(f"  BENCHMARK RESULTS: Mistral OCR vs LlamaParse")
    print(f"{'='*70}\n")
    print(f"  Total wall time: {grand_total:.1f}s ({grand_total/60:.1f} min)")
    print(f"  Documents: {len(pdfs)} | Pages: {total_pages}\n")

    hdr = f"  {'Document':<40} {'Pgs':>4} {'M-Time':>7} {'M-T/pg':>7} {'M-Chars':>9} {'L-Time':>7} {'L-T/pg':>7} {'L-Chars':>9}"
    print(hdr)
    print(f"  {'-'*40} {'-'*4} {'-'*7} {'-'*7} {'-'*9} {'-'*7} {'-'*7} {'-'*9}")

    m_ok = l_ok = 0
    m_total_time = l_total_time = 0.0
    m_total_chars = l_total_chars = 0

    for r in all_results:
        m = r.get("mistral", {})
        l = r.get("llama", {})
        m_time = f"{m.get('time_s', 0):.1f}s" if m.get("status") == "ok" else "FAIL"
        m_tpp = f"{m.get('time_per_page_s', 0):.2f}s" if m.get("status") == "ok" else "-"
        m_chars = f"{m.get('text_length', 0):,}" if m.get("status") == "ok" else "-"
        l_time = f"{l.get('time_s', 0):.1f}s" if l.get("status") == "ok" else "FAIL"
        l_tpp = f"{l.get('time_per_page_s', 0):.2f}s" if l.get("status") == "ok" else "-"
        l_chars = f"{l.get('text_length', 0):,}" if l.get("status") == "ok" else "-"

        print(f"  {r['document']:<40} {r['pages']:>4} {m_time:>7} {m_tpp:>7} {m_chars:>9} {l_time:>7} {l_tpp:>7} {l_chars:>9}")

        if m.get("status") == "ok":
            m_ok += 1
            m_total_time += m["time_s"]
            m_total_chars += m["text_length"]
        if l.get("status") == "ok":
            l_ok += 1
            l_total_time += l["time_s"]
            l_total_chars += l["text_length"]

    print(f"\n  {'TOTALS':<40} {total_pages:>4} {m_total_time:>6.1f}s {'':>7} {m_total_chars:>9,} {l_total_time:>6.1f}s {'':>7} {l_total_chars:>9,}")

    print(f"\n  Summary:")
    print(f"    Mistral: {m_ok}/{len(pdfs)} OK | {m_total_time:.1f}s total | {m_total_chars:,} chars | cost: ${total_pages * 0.001:.2f}")
    print(f"    Llama:   {l_ok}/{len(pdfs)} OK | {l_total_time:.1f}s total | {l_total_chars:,} chars | cost: ${total_pages * 3 * 0.00125:.2f}")

    # Save
    output_file = OUTPUT_DIR / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_pages": total_pages,
            "grand_total_time_s": round(grand_total, 2),
            "mistral": {"ok": m_ok, "total_time_s": round(m_total_time, 2), "total_chars": m_total_chars,
                        "cost_usd": round(total_pages * 0.001, 4)},
            "llama": {"ok": l_ok, "total_time_s": round(l_total_time, 2), "total_chars": l_total_chars,
                      "cost_usd": round(total_pages * 3 * 0.00125, 4)},
            "documents": all_results,
        }, f, indent=2)
    print(f"\n  Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
