from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi import UploadFile

from ..config import get_settings


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    value = value.strip("-").lower()
    return value or "file"


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.root = self.settings.storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def absolute_path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def public_path(self, relative_path: str) -> str:
        return f"/storage/{relative_path}"

    async def save_upload(self, case_id: str, document_id: str, file: UploadFile) -> dict:
        safe_name = slugify(file.filename or "document.pdf")
        relative_path = f"cases/{case_id}/documents/{document_id}/{safe_name}"
        absolute_path = self.absolute_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        if len(content) > self.settings.max_upload_size_bytes:
            raise ValueError(
                f"Upload exceeds max size of {self.settings.max_upload_size_mb} MB: {safe_name}"
            )
        absolute_path.write_bytes(content)
        return {
            "relative_path": relative_path,
            "absolute_path": absolute_path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "file_size_bytes": len(content),
            "mime_type": file.content_type or "application/pdf",
        }

    def save_page_image(self, case_id: str, document_id: str, page_number: int, image_bytes: bytes) -> str:
        relative_path = f"cases/{case_id}/documents/{document_id}/pages/page_{page_number}.png"
        absolute_path = self.absolute_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(image_bytes)
        return relative_path

    def save_report_file(self, case_id: str, report_id: str, extension: str, content: bytes) -> str:
        relative_path = f"cases/{case_id}/reports/{report_id}.{extension}"
        absolute_path = self.absolute_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)
        return relative_path


storage = StorageService()
