from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Intelli-Credit Copilot API"
    app_env: str = "development"
    app_url: str = "http://localhost:8000"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
    )

    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{(ROOT_DIR / 'backend' / 'app.db').as_posix()}"
    )

    storage_root: Path = ROOT_DIR / "backend" / "storage"
    storage_bucket: str = "intelli-credit-docs"
    max_upload_size_mb: int = 50
    document_processing_backend: str = "docling_remote"
    document_processing_max_workers: int = 8
    document_batch_max_concurrency: int = 4
    MARKER_API_URL: str = "http://127.0.0.1:8001"

    gemini_api_key: str | None = None
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_vision_model: str = "gemini-2.5-flash"
    gemini_context_char_limit: int = 200_000
    classification_require_llm: bool = True
    landing_ai_api_key: str | None = None
    firecrawl_api_key: str = ""
    research_max_results: int = 18
    research_timeout_seconds: float = 20.0
    research_min_entity_match_score: float = 0.55
    research_contextual_match_score: float = 0.30
    research_max_pages_to_scrape: int = 16
    sentry_dsn: str | None = None
    request_id_header: str = "X-Request-ID"
    supabase_url: str | None = None
    supabase_key: str | None = None
    api_key: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("sqlite:///"):
            return value.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
