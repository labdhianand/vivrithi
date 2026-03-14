from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import get_settings

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - optional runtime dependency
    genai = None
    types = None


def get_gemini_client():
    settings = get_settings()
    if genai is None or not settings.gemini_api_key:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


def generate_text(prompt: str, model: str | None = None, response_mime_type: str | None = None) -> str | None:
    client = get_gemini_client()
    if client is None:
        return None
    settings = get_settings()
    kwargs: dict[str, Any] = {}
    if response_mime_type and types is not None:
        kwargs["config"] = types.GenerateContentConfig(response_mime_type=response_mime_type)
    response = client.models.generate_content(
        model=model or settings.gemini_text_model,
        contents=prompt,
        **kwargs,
    )
    return getattr(response, "text", None)


def generate_json(prompt: str, model: str | None = None) -> Any | None:
    text = generate_text(prompt, model=model, response_mime_type="application/json")
    if not text:
        return None
    normalized = text.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:json)?\s*", "", normalized)
        normalized = re.sub(r"\s*```$", "", normalized)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", normalized, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None


def generate_from_file(
    prompt: str,
    file_path: Path,
    model: str | None = None,
    response_mime_type: str | None = None,
) -> str | None:
    client = get_gemini_client()
    if client is None:
        return None
    settings = get_settings()
    uploaded = client.files.upload(file=file_path)
    kwargs: dict[str, Any] = {}
    if response_mime_type and types is not None:
        kwargs["config"] = types.GenerateContentConfig(response_mime_type=response_mime_type)
    response = client.models.generate_content(
        model=model or settings.gemini_vision_model,
        contents=[prompt, uploaded],
        **kwargs,
    )
    return getattr(response, "text", None)
