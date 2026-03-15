from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.database import Base, get_session
from backend.app.main import app
from backend.app.models.case import Case
from backend.app.models.document import Document
from backend.app.models.extraction import Extraction
from backend.app.services.databricks import DatabricksService
from backend.app.services.extractor import extract_with_schema
from backend.app.services.markdown_builder import build_document_markdown
from backend.app.services.recommendation import build_improvement_scenarios
from backend.app.services.storage import storage
from backend.app.services.types import ParsedPage, ParsedTable


def test_request_tracing_adds_request_id_header() -> None:
    async def _run() -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers["X-Request-ID"]

    asyncio.run(_run())


def test_upload_respects_max_size_limit(tmp_path, monkeypatch) -> None:
    async def _run() -> None:
        db_path = tmp_path / "app.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        storage_root = tmp_path / "storage"
        storage_root.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(storage, "root", storage_root)
        original_limit_mb = storage.settings.max_upload_size_mb
        monkeypatch.setattr(storage.settings, "max_upload_size_mb", 0)

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        try:
            async with session_factory() as session:
                session.add(Case(id="case-upload", company_name="Upload Demo"))
                await session.commit()

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post(
                    "/api/cases/case-upload/documents/upload",
                    files={"files": ("too-big.pdf", b"x", "application/pdf")},
                )
            assert response.status_code == 413
            assert "max size" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
            monkeypatch.setattr(storage.settings, "max_upload_size_mb", original_limit_mb)
            await engine.dispose()

    asyncio.run(_run())


def test_retry_failed_document_and_failed_jobs_listing(tmp_path, monkeypatch) -> None:
    async def _run() -> None:
        db_path = tmp_path / "app.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        monkeypatch.setattr("backend.app.api.documents._enqueue_case_processing", lambda *args, **kwargs: None)
        app.dependency_overrides[get_session] = override_session
        try:
            async with session_factory() as session:
                case = Case(id="case-failed", company_name="Failed Ops Co")
                document = Document(
                    id="doc-failed",
                    case_id=case.id,
                    original_filename="broken.pdf",
                    stored_path="cases/case-failed/documents/doc-failed/broken.pdf",
                    processing_status="failed",
                    failure_reason="remote gpu timeout",
                    classification_status="pending",
                )
                session.add(case)
                session.add(document)
                await session.commit()

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                failed_response = await client.get("/api/ops/failed-jobs/documents")
                assert failed_response.status_code == 200
                payload = failed_response.json()
                assert payload["total_failed_documents"] == 1
                assert payload["items"][0]["failure_reason"] == "remote gpu timeout"

                retry_response = await client.post("/api/documents/doc-failed/retry")
                assert retry_response.status_code == 200
                retry_payload = retry_response.json()
                assert retry_payload["document"]["processing_status"] == "queued"
                assert retry_payload["document"]["failure_reason"] is None
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(_run())


def test_update_extraction_sets_correction_type(tmp_path) -> None:
    async def _run() -> None:
        db_path = tmp_path / "app.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async def override_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        try:
            async with session_factory() as session:
                case = Case(id="case-extract", company_name="Extraction Co")
                document = Document(
                    id="doc-extract",
                    case_id=case.id,
                    original_filename="doc.pdf",
                    stored_path="cases/case-extract/documents/doc-extract/doc.pdf",
                    processing_status="extracted",
                    classification_status="approved",
                )
                extraction = Extraction(
                    id="ext-1",
                    document_id=document.id,
                    schema_field_key="lcr_ratio",
                    value="151.7%",
                    value_type="percentage",
                )
                session.add(case)
                session.add(document)
                session.add(extraction)
                await session.commit()

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.patch(
                    "/api/extractions/ext-1",
                    json={"user_edited_value": "152.1%", "user_verified": True},
                )
            assert response.status_code == 200
            assert response.json()["correction_type"] == "value_changed"
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(_run())


def test_extract_with_schema_preserves_spreadsheet_evidence() -> None:
    rows = [
        ["Metric", "Q3 FY26", "Q2 FY26"],
        ["Gross NPA", "1.8%", "1.9%"],
    ]
    page = ParsedPage(
        page_number=1,
        text="Gross NPA 1.8%",
        markdown="",
        tables=[ParsedTable(bbox=(0.0, 0.0, 1.0, 1.0), rows=rows, markdown="", sheet_name="Performance")],
        bounding_boxes=[],
    )

    results = asyncio.run(
        extract_with_schema(
            pdf_path=Path("portfolio.csv"),
            document_markdown=build_document_markdown([page]),
            schema={
                "category": "Portfolio_Performance",
                "fields": [{"key": "gnpa_percent", "label": "GNPA %", "type": "percentage", "required": True}],
            },
            pages=[page],
        )
    )

    assert results[0].value == "1.8%"
    assert results[0].sheet_name == "Performance"
    assert results[0].row_label == "Gross NPA"
    assert results[0].column_header == "Q3 FY26"
    assert results[0].cell_reference == "B2"


def test_databricks_stub_builds_case_queries_and_unconfigured_health() -> None:
    service = DatabricksService()
    health = asyncio.run(service.healthcheck())
    assert health.configured is False
    assert health.reachable is False

    case = SimpleNamespace(
        company_name="Acme Finance Limited",
        cin="L12345KA2010PLC000001",
        pan="AACCA1234A",
    )
    queries = service.build_case_query_templates(case)
    assert "gst_returns" in queries
    assert "income_tax_returns" in queries["itr"]
    assert case.pan in queries["bank_statements"]


def test_recommendation_improvement_scenarios_are_actionable() -> None:
    five_cs = {
        "character": SimpleNamespace(score=45),
        "capacity": SimpleNamespace(score=52),
        "capital": SimpleNamespace(score=54),
        "collateral": SimpleNamespace(score=40),
        "conditions": SimpleNamespace(score=48),
    }
    cross_checks = [
        {"check_name": "GST-Revenue Reasonableness", "status": "mismatch"},
        {"check_name": "Rating Presence", "status": "mismatch"},
    ]
    hard_stops = ["High severity legal findings present.", "Current rating not clearly evidenced."]

    scenarios = build_improvement_scenarios(five_cs, cross_checks, hard_stops)

    assert scenarios
    titles = {item["title"] for item in scenarios}
    assert "Resolve verified legal findings" in titles
    assert "Evidence the current rating position" in titles
