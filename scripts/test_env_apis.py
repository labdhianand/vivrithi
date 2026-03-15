#!/usr/bin/env python3
"""Smoke-test the API integrations configured in a .env file.

The script focuses on the services documented in `reference/v1/api.md`:
- Qdrant
- Firecrawl
- LandingAI
- Sarvam
- OpenRouter

Usage:
    python3 scripts/test_env_apis.py
    python3 scripts/test_env_apis.py --only firecrawl,openrouter
    python3 scripts/test_env_apis.py --json
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_LANDINGAI_ENDPOINT = "https://api.va.landing.ai/v1"
DEFAULT_SARVAM_BASE_URL = "https://api.sarvam.ai"
DEFAULT_FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"


class SmokeTestError(Exception):
    """Raised for provider-specific request or validation failures."""

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        detail: str | None = None,
        elapsed_ms: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.detail = detail
        self.elapsed_ms = elapsed_ms


@dataclass
class HttpResponse:
    status_code: int
    elapsed_ms: int
    headers: dict[str, str]
    text: str
    json_body: Any | None


@dataclass
class Result:
    service: str
    status: str
    summary: str
    http_status: int | None = None
    elapsed_ms: int | None = None
    detail: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Path to the .env file to load. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout in seconds. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated subset of services to test.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text table.",
    )
    parser.add_argument(
        "--sample-pdf",
        default="",
        help="Optional PDF path to use for the LandingAI upload test.",
    )
    return parser.parse_args()


def load_env(env_file: Path) -> dict[str, str]:
    env_values: dict[str, str] = {}
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if value and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            env_values[key] = value

    merged_env = dict(env_values)
    for key, value in os.environ.items():
        merged_env[key] = value
    return merged_env


def env_value(env: dict[str, str], key: str, default: str = "") -> str:
    return env.get(key, default).strip()


def join_url(base: str, *parts: str) -> str:
    clean_base = base.rstrip("/")
    clean_parts = [part.strip("/") for part in parts if part]
    if not clean_parts:
        return clean_base
    return clean_base + "/" + "/".join(clean_parts)


def truncate(value: str | None, limit: int = 240) -> str | None:
    if value is None:
        return None
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def maybe_json(text: str) -> Any | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def request_http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: Any | None = None,
    raw_body: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HttpResponse:
    if json_body is not None and raw_body is not None:
        raise ValueError("json_body and raw_body are mutually exclusive")

    final_headers = {"User-Agent": "vivriti-api-smoke-test/1.0"}
    if headers:
        final_headers.update(headers)

    body = raw_body
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")

    req = request.Request(url, data=body, headers=final_headers, method=method)
    started = time.perf_counter()

    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = response.read()
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            text = payload.decode("utf-8", errors="replace")
            return HttpResponse(
                status_code=response.status,
                elapsed_ms=elapsed_ms,
                headers=dict(response.headers.items()),
                text=text,
                json_body=maybe_json(text),
            )
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise SmokeTestError(
            f"HTTP {exc.code} from {url}",
            http_status=exc.code,
            detail=truncate(payload),
            elapsed_ms=elapsed_ms,
        ) from exc
    except error.URLError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise SmokeTestError(
            f"Network error for {url}: {exc.reason}",
            detail=truncate(str(exc.reason)),
            elapsed_ms=elapsed_ms,
        ) from exc
    except (TimeoutError, socket.timeout) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise SmokeTestError(
            f"Request timed out for {url}",
            detail=truncate(str(exc) or "The remote service did not respond before the timeout"),
            elapsed_ms=elapsed_ms,
        ) from exc


def require_dict(response: HttpResponse, service: str) -> dict[str, Any]:
    if not isinstance(response.json_body, dict):
        raise SmokeTestError(
            f"{service} returned a non-JSON or non-object response",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )
    return response.json_body


def config_state(
    env: dict[str, str],
    *,
    required: list[str],
    optional: list[str] | None = None,
) -> tuple[str, list[str]]:
    optional = optional or []
    all_keys = required + optional
    populated = [key for key in all_keys if env_value(env, key)]
    if not populated:
        return "skip", []
    missing_required = [key for key in required if not env_value(env, key)]
    if missing_required:
        return "config", missing_required
    return "ok", []


def build_multipart(
    *,
    fields: dict[str, str] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
) -> tuple[bytes, str]:
    fields = fields or {}
    files = files or {}
    boundary = f"----vivriti-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for name, (filename, payload, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                payload,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def find_sample_pdf(root_dir: Path, override_path: str) -> Path | None:
    if override_path:
        candidate = Path(override_path).expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate
        raise SmokeTestError(
            f"LandingAI sample PDF was not found: {candidate}",
            detail="Use --sample-pdf with an existing file path.",
        )

    data_dir = root_dir / "data"
    if not data_dir.exists():
        return None

    pdf_paths = [path for path in data_dir.rglob("*.pdf") if path.is_file()]
    if not pdf_paths:
        return None
    return min(pdf_paths, key=lambda path: path.stat().st_size)


def make_skip(service: str, reason: str) -> Result:
    return Result(service=service, status="SKIP", summary=reason)


def make_config(service: str, missing_keys: list[str]) -> Result:
    joined = ", ".join(missing_keys)
    return Result(
        service=service,
        status="CONFIG",
        summary=f"incomplete configuration: missing {joined}",
    )


def check_qdrant(env: dict[str, str], timeout: float, _: str) -> Result:
    status, missing = config_state(env, required=["QDRANT_URL"], optional=["QDRANT_API_KEY", "QDRANT_COLLECTION"])
    if status == "skip":
        return make_skip("qdrant", "QDRANT_URL is not set")
    if status == "config":
        return make_config("qdrant", missing)

    headers: dict[str, str] = {}
    api_key = env_value(env, "QDRANT_API_KEY")
    if api_key:
        headers["api-key"] = api_key

    response = request_http(
        "GET",
        join_url(env_value(env, "QDRANT_URL"), "collections"),
        headers=headers,
        timeout=timeout,
    )
    payload = require_dict(response, "Qdrant")
    collections = payload.get("result", {}).get("collections", [])
    names = [item.get("name") for item in collections if isinstance(item, dict)]
    target_collection = env_value(env, "QDRANT_COLLECTION")

    if target_collection:
        if target_collection in names:
            summary = f"reachable; target collection '{target_collection}' exists"
        else:
            summary = (
                f"reachable; target collection '{target_collection}' was not found "
                f"among {len(names)} collections"
            )
    else:
        summary = f"reachable; listed {len(names)} collections"

    return Result(
        service="qdrant",
        status="PASS",
        summary=summary,
        http_status=response.status_code,
        elapsed_ms=response.elapsed_ms,
    )


def check_firecrawl(env: dict[str, str], timeout: float, _: str) -> Result:
    status, missing = config_state(env, required=["FIRECRAWL_API_KEY"])
    if status == "skip":
        return make_skip("firecrawl", "FIRECRAWL_API_KEY is not set")
    if status == "config":
        return make_config("firecrawl", missing)

    response = request_http(
        "POST",
        DEFAULT_FIRECRAWL_SCRAPE_URL,
        headers={"Authorization": f"Bearer {env_value(env, 'FIRECRAWL_API_KEY')}"},
        json_body={
            "url": "https://example.com",
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
        timeout=timeout,
    )
    payload = require_dict(response, "Firecrawl")
    if payload.get("success") is False:
        raise SmokeTestError(
            "Firecrawl reported an unsuccessful scrape",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )

    markdown = ""
    data = payload.get("data")
    if isinstance(data, dict):
        markdown = str(data.get("markdown", "")).strip()
    if not markdown:
        raise SmokeTestError(
            "Firecrawl response did not include scraped markdown",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )

    return Result(
        service="firecrawl",
        status="PASS",
        summary=f"scrape succeeded; returned {len(markdown)} markdown characters",
        http_status=response.status_code,
        elapsed_ms=response.elapsed_ms,
    )


def check_landingai(env: dict[str, str], timeout: float, sample_pdf_override: str) -> Result:
    status, missing = config_state(env, required=["LANDINGAI_API_KEY"], optional=["LANDINGAI_ENDPOINT"])
    if status == "skip":
        return make_skip("landingai", "LANDINGAI_API_KEY is not set")
    if status == "config":
        return make_config("landingai", missing)

    sample_pdf = find_sample_pdf(ROOT_DIR, sample_pdf_override)
    if sample_pdf is None:
        raise SmokeTestError("No sample PDF was found under ./data for the LandingAI test")

    mime_type = mimetypes.guess_type(sample_pdf.name)[0] or "application/pdf"
    multipart_body, content_type = build_multipart(
        fields={"model": "dpt-2"},
        files={"document": (sample_pdf.name, sample_pdf.read_bytes(), mime_type)},
    )

    endpoint = env_value(env, "LANDINGAI_ENDPOINT", DEFAULT_LANDINGAI_ENDPOINT)
    landingai_timeout = max(timeout, 90.0)
    response = request_http(
        "POST",
        join_url(endpoint, "ade", "parse"),
        headers={
            "Authorization": f"Basic {env_value(env, 'LANDINGAI_API_KEY')}",
            "Content-Type": content_type,
        },
        raw_body=multipart_body,
        timeout=landingai_timeout,
    )
    payload = require_dict(response, "LandingAI")
    blocks = payload.get("blocks")
    markdown = payload.get("markdown")
    if isinstance(blocks, list):
        summary = f"document parse succeeded using '{sample_pdf.name}'; received {len(blocks)} block(s)"
    elif isinstance(markdown, str) and markdown.strip():
        summary = (
            f"document parse succeeded using '{sample_pdf.name}'; "
            f"returned {len(markdown.strip())} markdown characters"
        )
    else:
        raise SmokeTestError(
            "LandingAI response did not include blocks or markdown",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )

    return Result(
        service="landingai",
        status="PASS",
        summary=summary,
        http_status=response.status_code,
        elapsed_ms=response.elapsed_ms,
    )


def check_sarvam(env: dict[str, str], timeout: float, _: str) -> Result:
    status, missing = config_state(env, required=["SARVAM_API_KEY"], optional=["SARVAM_BASE_URL"])
    if status == "skip":
        return make_skip("sarvam", "SARVAM_API_KEY is not set")
    if status == "config":
        return make_config("sarvam", missing)

    base_url = env_value(env, "SARVAM_BASE_URL", DEFAULT_SARVAM_BASE_URL)
    response = request_http(
        "POST",
        join_url(base_url, "text-lid"),
        headers={"api-subscription-key": env_value(env, "SARVAM_API_KEY")},
        json_body={"input": "Hello from the Vivriti API smoke test."},
        timeout=timeout,
    )
    payload = require_dict(response, "Sarvam")
    language_code = payload.get("language_code")
    if not language_code:
        raise SmokeTestError(
            "Sarvam response did not include language_code",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )

    return Result(
        service="sarvam",
        status="PASS",
        summary=f"text-lid succeeded; detected language '{language_code}'",
        http_status=response.status_code,
        elapsed_ms=response.elapsed_ms,
    )


def check_openrouter(env: dict[str, str], timeout: float, _: str) -> Result:
    status, missing = config_state(env, required=["OPENROUTER_API_KEY"], optional=["OPENROUTER_BASE_URL", "OPENROUTER_MODEL"])
    if status == "skip":
        return make_skip("openrouter", "OPENROUTER_API_KEY is not set")
    if status == "config":
        return make_config("openrouter", missing)

    base_url = env_value(env, "OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL)
    response = request_http(
        "GET",
        join_url(base_url, "models"),
        headers={"Authorization": f"Bearer {env_value(env, 'OPENROUTER_API_KEY')}"},
        timeout=timeout,
    )
    payload = require_dict(response, "OpenRouter")
    models = payload.get("data")
    if not isinstance(models, list):
        raise SmokeTestError(
            "OpenRouter response did not include a data list",
            http_status=response.status_code,
            detail=truncate(response.text),
            elapsed_ms=response.elapsed_ms,
        )

    configured_model = env_value(env, "OPENROUTER_MODEL")
    if configured_model:
        model_ids = {item.get("id") for item in models if isinstance(item, dict)}
        if configured_model not in model_ids:
            raise SmokeTestError(
                f"Configured OpenRouter model '{configured_model}' was not returned by /models",
                http_status=response.status_code,
                elapsed_ms=response.elapsed_ms,
            )
        summary = f"models endpoint succeeded; configured model '{configured_model}' is available"
    else:
        summary = f"models endpoint succeeded; received {len(models)} model entries"

    return Result(
        service="openrouter",
        status="PASS",
        summary=summary,
        http_status=response.status_code,
        elapsed_ms=response.elapsed_ms,
    )


CHECKS: dict[str, Callable[[dict[str, str], float, str], Result]] = {
    "qdrant": check_qdrant,
    "firecrawl": check_firecrawl,
    "landingai": check_landingai,
    "sarvam": check_sarvam,
    "openrouter": check_openrouter,
}


def resolve_services(only_arg: str) -> list[str]:
    if not only_arg.strip():
        return list(CHECKS)

    selected = []
    for item in only_arg.split(","):
        service = item.strip().lower()
        if not service:
            continue
        if service not in CHECKS:
            valid = ", ".join(CHECKS)
            raise SystemExit(f"Unknown service '{service}'. Valid services: {valid}")
        selected.append(service)
    return selected


def format_table(results: list[Result]) -> str:
    rows = [
        [
            result.service,
            result.status,
            str(result.http_status or ""),
            str(result.elapsed_ms or ""),
            result.summary,
        ]
        for result in results
    ]
    headers = ["service", "status", "http", "ms", "summary"]
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    def render_row(values: list[str]) -> str:
        return "  ".join(value.ljust(widths[idx]) for idx, value in enumerate(values))

    lines = [render_row(headers), render_row(["-" * width for width in widths])]
    lines.extend(render_row(row) for row in rows)

    details = []
    for result in results:
        if result.detail:
            details.append(f"{result.service}: {result.detail}")
    if details:
        lines.append("")
        lines.extend(details)

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    env_file = Path(args.env_file).expanduser()
    env = load_env(env_file)
    services = resolve_services(args.only)

    results: list[Result] = []
    for service in services:
        check = CHECKS[service]
        try:
            results.append(check(env, args.timeout, args.sample_pdf))
        except SmokeTestError as exc:
            results.append(
                Result(
                    service=service,
                    status="FAIL",
                    summary=exc.message,
                    http_status=exc.http_status,
                    elapsed_ms=exc.elapsed_ms,
                    detail=exc.detail,
                )
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            results.append(
                Result(
                    service=service,
                    status="FAIL",
                    summary=f"unexpected error: {type(exc).__name__}",
                    detail=truncate(str(exc)),
                )
            )

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        print(format_table(results))

    failing_statuses = {"FAIL", "CONFIG"}
    return 1 if any(result.status in failing_statuses for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
