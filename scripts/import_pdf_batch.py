#!/usr/bin/env python3
"""Download a manifest of official PDF documents into the corpus.

The manifest must be a CSV with the columns:
company, range, doc_type, period, doc_title, source_page, source_url, local_path
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib import error, parse, request


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT_DIR / "data/challenge_doc_corpus/catalog/official_pdf_batch_2026-03-10.csv"
DEFAULT_REPORT = ROOT_DIR / "data/challenge_doc_corpus/catalog/official_pdf_batch_2026-03-10_downloads.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class DownloadResult:
    company: str
    doc_type: str
    period: str
    doc_title: str
    source_url: str
    local_path: str
    status: str
    size_bytes: int | None = None
    sha256: str | None = None
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="CSV manifest to download. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT),
        help="JSON report output path. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-download timeout in seconds. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already exist on disk.",
    )
    return parser.parse_args()


def normalized_url(raw_url: str) -> str:
    parts = parse.urlsplit(raw_url)
    path = parse.quote(parts.path, safe="/%")
    query = parse.quote_plus(parts.query, safe="=&%")
    return parse.urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fetch_pdf(url: str, timeout: float) -> bytes:
    req = request.Request(
        normalized_url(url),
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": parse.urlunsplit(parse.urlsplit(url)._replace(path="", query="", fragment="")),
        },
    )
    with request.urlopen(req, timeout=timeout) as response:
        payload = response.read()
    if not payload.startswith(b"%PDF"):
        raise ValueError("response was not a PDF")
    return payload


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser()
    report_path = Path(args.report).expanduser()

    rows = load_manifest(manifest_path)
    results: list[DownloadResult] = []

    for row in rows:
        local_path = ROOT_DIR / row["local_path"]
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if args.skip_existing and local_path.exists():
            payload = local_path.read_bytes()
            results.append(
                DownloadResult(
                    company=row["company"],
                    doc_type=row["doc_type"],
                    period=row["period"],
                    doc_title=row["doc_title"],
                    source_url=row["source_url"],
                    local_path=row["local_path"],
                    status="skipped_existing",
                    size_bytes=len(payload),
                    sha256=sha256_hex(payload),
                )
            )
            continue

        try:
            payload = fetch_pdf(row["source_url"], args.timeout)
            local_path.write_bytes(payload)
            results.append(
                DownloadResult(
                    company=row["company"],
                    doc_type=row["doc_type"],
                    period=row["period"],
                    doc_title=row["doc_title"],
                    source_url=row["source_url"],
                    local_path=row["local_path"],
                    status="downloaded",
                    size_bytes=len(payload),
                    sha256=sha256_hex(payload),
                )
            )
        except (error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
            if local_path.exists():
                local_path.unlink()
            results.append(
                DownloadResult(
                    company=row["company"],
                    doc_type=row["doc_type"],
                    period=row["period"],
                    doc_title=row["doc_title"],
                    source_url=row["source_url"],
                    local_path=row["local_path"],
                    status="failed",
                    error=str(exc),
                )
            )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps([asdict(item) for item in results], indent=2), encoding="utf-8")

    for item in results:
        print(f"{item.status:16} {item.company:20} {item.doc_type:28} {item.local_path}")
        if item.error:
            print(f"  error: {item.error}")

    failures = [item for item in results if item.status == "failed"]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
