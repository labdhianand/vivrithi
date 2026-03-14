#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a document artifact from the fast runtime or Docling.")
    parser.add_argument("pdf_path", help="PDF path to process.")
    parser.add_argument("--backend", choices=["fast", "docling"], default="fast")
    parser.add_argument("--category", default=None, help="Forced schema category for the fast backend.")
    parser.add_argument("--workers", type=int, default=8, help="Worker count for the fast backend.")
    parser.add_argument("--output", required=True, help="JSON output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("GEMINI_API_KEY", "")

    from backend.app.config import get_settings
    from backend.app.services.runtime import build_docling_artifact, build_fast_artifact

    get_settings.cache_clear()
    pdf_path = Path(args.pdf_path).expanduser()
    output_path = Path(args.output).expanduser()

    if args.backend == "fast":
        artifact = asyncio.run(build_fast_artifact(pdf_path, category=args.category, max_workers=args.workers))
    else:
        artifact = build_docling_artifact(pdf_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact.to_dict(), indent=2), encoding="utf-8")
    print(f"saved_artifact={output_path}")
    print(f"backend={artifact.backend} pages={artifact.page_count} blocks={len(artifact.text_blocks)} tables={len(artifact.tables)} chunks={len(artifact.chunks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
