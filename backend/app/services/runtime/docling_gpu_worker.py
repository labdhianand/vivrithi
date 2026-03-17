from __future__ import annotations

import argparse
import asyncio
import json

from .docling_remote import check_marker_health


async def convert_document(_: argparse.Namespace | None = None) -> dict:
    healthy = await check_marker_health()
    return {
        "backend": "pdfplumber",
        "healthy": healthy,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local pdfplumber parser health.")
    return parser.parse_args()


def main() -> int:
    payload = asyncio.run(convert_document(parse_args()))
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
