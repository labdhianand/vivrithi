from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from .api.router import router as api_router
from .config import get_settings
from .database import init_db


settings = get_settings()
logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
    except Exception:
        logger.warning("Sentry DSN configured but sentry_sdk is not installed.")
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment=settings.app_env,
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Lightweight API key check for /api/ routes. Only enforced when api_key is set."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.api_key:
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        provided = request.headers.get("X-API-Key", "")
        if provided != settings.api_key:
            return Response(content='{"detail":"Invalid or missing API key"}', status_code=401, media_type="application/json")
        return await call_next(request)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Unhandled request failure",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
                headers={settings.request_id_header: request_id},
            )
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers[settings.request_id_header] = request_id
        logger.info(
            "Request complete",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    _init_sentry()
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
app.mount("/storage", StaticFiles(directory=settings.storage_root), name="storage")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
