from __future__ import annotations

from typing import Any

from ..config import get_settings
from .gemini import generate_json as generate_gemini_json


def has_text_llm() -> bool:
    settings = get_settings()
    return bool(settings.gemini_api_key)


def generate_json(prompt: str, model: str | None = None) -> Any | None:
    settings = get_settings()
    if settings.gemini_api_key:
        return generate_gemini_json(prompt, model=model or settings.gemini_text_model)
    return None
