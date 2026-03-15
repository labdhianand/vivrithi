from __future__ import annotations

import asyncio
import json
import posixpath
import shlex
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncssh

from ...config import get_settings
from ..types import ParsedPage, ParsedTable


@dataclass(slots=True)
class RemoteDoclingResult:
    markdown: str
    text: str
    page_count: int
    convert_seconds: float
    payload: dict[str, Any]


class DoclingRemoteBackend:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.worker_path = Path(__file__).with_name("docling_gpu_worker.py")
        self._bootstrap_lock = asyncio.Lock()
        self._bootstrap_complete = False
        self._resolved_home: str | None = None

    def _connect_options(self) -> dict[str, Any]:
        if not self.settings.docling_remote_host or not self.settings.docling_remote_username:
            raise RuntimeError("Docling remote host and username must be configured.")
        options: dict[str, Any] = {
            "host": self.settings.docling_remote_host,
            "port": self.settings.docling_remote_port,
            "username": self.settings.docling_remote_username,
            "known_hosts": None if not self.settings.docling_remote_known_hosts else self.settings.docling_remote_known_hosts,
        }
        if self.settings.docling_remote_password:
            options["password"] = self.settings.docling_remote_password
        if self.settings.docling_remote_client_key_path:
            options["client_keys"] = [self.settings.docling_remote_client_key_path]
        return options

    async def _connect(self) -> asyncssh.SSHClientConnection:
        return await asyncssh.connect(**self._connect_options())

    async def _remote_home(self) -> str:
        if self._resolved_home is not None:
            return self._resolved_home
        async with await self._connect() as conn:
            result = await conn.run("printf %s \"$HOME\"", check=False)
            if result.exit_status != 0 or not result.stdout.strip():
                raise RuntimeError("Failed to resolve remote home directory.")
            self._resolved_home = result.stdout.strip()
        return self._resolved_home

    async def _resolve_remote_path(self, value: str) -> str:
        if value == "~" or value.startswith("~/"):
            home = await self._remote_home()
            suffix = value[2:] if value.startswith("~/") else ""
            return posixpath.join(home, suffix) if suffix else home
        return value

    async def _ensure_remote_ready(self) -> None:
        if self._bootstrap_complete or not self.settings.docling_remote_enable_bootstrap:
            return
        async with self._bootstrap_lock:
            if self._bootstrap_complete:
                return
            workspace = await self._resolve_remote_path(self.settings.docling_remote_workspace)
            venv = await self._resolve_remote_path(self.settings.docling_remote_venv)
            python_bin = self.settings.docling_remote_python_bin
            torch_index = self.settings.docling_remote_bootstrap_torch_index_url
            bootstrap_script = f"""
set -euo pipefail
WORKSPACE={shlex.quote(workspace)}
VENV={shlex.quote(venv)}
PYTHON_BIN={shlex.quote(python_bin)}
mkdir -p "$WORKSPACE"
if [ ! -x "$VENV/bin/python" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi
source "$VENV/bin/activate"
python -m pip install --upgrade pip setuptools wheel
if ! python - <<'PY'
import sys
try:
    import docling  # noqa: F401
    import torch
    assert torch.cuda.is_available()
except Exception:
    sys.exit(1)
PY
then
  python -m pip install --upgrade torch torchvision torchaudio --index-url {shlex.quote(torch_index)}
  python -m pip install --upgrade "docling[rapidocr]"
fi
"""
            async with await self._connect() as conn:
                result = await conn.run(f"bash -lc {shlex.quote(bootstrap_script)}", check=False)
                if result.exit_status != 0:
                    raise RuntimeError(
                        "Failed to bootstrap remote Docling environment: "
                        f"{result.stderr or result.stdout or 'unknown error'}"
                    )
            self._bootstrap_complete = True

    async def convert(self, source_path: Path) -> RemoteDoclingResult:
        await self._ensure_remote_ready()
        workspace = await self._resolve_remote_path(self.settings.docling_remote_workspace)
        venv = await self._resolve_remote_path(self.settings.docling_remote_venv)
        run_id = str(uuid.uuid4())
        remote_run_dir = f"{workspace}/runs/{run_id}"
        remote_input = f"{remote_run_dir}/{source_path.name}"
        remote_output = f"{remote_run_dir}/result.json"
        remote_worker = f"{workspace}/docling_gpu_worker.py"
        async with await self._connect() as conn:
            async with conn.start_sftp_client() as sftp:
                await sftp.makedirs(remote_run_dir, exist_ok=True)
                await sftp.put(str(self.worker_path), remote_worker)
                await sftp.put(str(source_path), remote_input)
            command = (
                "set -euo pipefail\n"
                f"source {shlex.quote(venv)}/bin/activate\n"
                f"python {shlex.quote(remote_worker)} "
                f"--input-path {shlex.quote(remote_input)} "
                f"--output-path {shlex.quote(remote_output)} "
                f"--page-batch-size {self.settings.docling_remote_page_batch_size} "
                f"--layout-batch-size {self.settings.docling_remote_layout_batch_size} "
                f"--ocr-batch-size {self.settings.docling_remote_ocr_batch_size} "
                f"--table-batch-size {self.settings.docling_remote_table_batch_size}\n"
            )
            result = await asyncio.wait_for(
                conn.run(f"bash -lc {shlex.quote(command)}", check=False),
                timeout=self.settings.docling_remote_document_timeout_seconds,
            )
            if result.exit_status != 0:
                raise RuntimeError(
                    "Remote Docling conversion failed: "
                    f"{result.stderr or result.stdout or 'unknown error'}"
                )
            async with conn.start_sftp_client() as sftp:
                remote_file = await sftp.open(remote_output, "r")
                raw_payload = await remote_file.read()
                await remote_file.close()
                await conn.run(f"rm -rf {shlex.quote(remote_run_dir)}", check=False)

        payload = json.loads(raw_payload)
        return RemoteDoclingResult(
            markdown=payload.get("markdown", ""),
            text=payload.get("text", ""),
            page_count=int(payload.get("page_count", 0)),
            convert_seconds=float(payload.get("convert_seconds", 0.0)),
            payload=payload,
        )


def parsed_pages_from_remote_payload(payload: dict[str, Any]) -> list[ParsedPage]:
    parsed_pages: list[ParsedPage] = []
    for page in payload.get("pages", []):
        tables = [
            ParsedTable(
                bbox=tuple(table.get("bbox") or [0.0, 0.0, 1.0, 1.0]),
                rows=table.get("rows") or [],
                markdown=table.get("markdown") or "",
                sheet_name=table.get("sheet_name"),
            )
            for table in page.get("tables", [])
        ]
        parsed_pages.append(
            ParsedPage(
                page_number=int(page["page_number"]),
                text=page.get("text") or "",
                markdown=page.get("markdown") or "",
                tables=tables,
                bounding_boxes=page.get("bounding_boxes") or [],
                parser_used="docling_gpu_remote",
                confidence=0.94,
            )
        )
    return parsed_pages


_remote_backend: DoclingRemoteBackend | None = None


def get_docling_remote_backend() -> DoclingRemoteBackend:
    global _remote_backend
    if _remote_backend is None:
        _remote_backend = DoclingRemoteBackend()
    return _remote_backend
