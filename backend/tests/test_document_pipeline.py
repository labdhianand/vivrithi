from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.database import Base
from backend.app.models.case import Case
from backend.app.models.document import Document
from backend.app.models.extraction import Extraction
from backend.app.models.page import Page
from backend.app.services.document_pipeline import _normalize_bbox, process_document
from backend.app.services.storage import storage
from backend.app.services.types import ClassificationResult, ExtractionResult


def test_normalize_bbox_pads_short_tuples() -> None:
    assert _normalize_bbox((0.1, 0.2)) == (0.1, 0.2, None, None)


def test_normalize_bbox_rejects_non_sequences() -> None:
    assert _normalize_bbox("0.1,0.2,0.3,0.4") == (None, None, None, None)


def test_process_document_fast_runtime_persists_pages_and_extractions(tmp_path, monkeypatch) -> None:
    async def _run() -> None:
        db_path = tmp_path / "app.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        storage_root = tmp_path / "storage"
        storage_root.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(storage, "root", storage_root)

        source_pdf = Path("claude_data/Aavas_Financiers/ALM/Disclosure_on_Liquidity_Coverage_Ratio_Q3_FY26.pdf")
        relative_pdf_path = "cases/case-1/documents/doc-1/alm.pdf"
        absolute_pdf_path = storage.absolute_path(relative_pdf_path)
        absolute_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_pdf_path.write_bytes(source_pdf.read_bytes())

        async with session_factory() as session:
            case = Case(id="case-1", company_name="Aavas Financiers Limited", sector="Housing Finance")
            document = Document(
                id="doc-1",
                case_id=case.id,
                original_filename=source_pdf.name,
                stored_path=relative_pdf_path,
                processing_status="pending",
                classification_status="pending",
            )
            session.add(case)
            session.add(document)
            await session.commit()
            await session.refresh(case)
            await session.refresh(document)

            processed = await process_document(session, case, document, backend="fast_runtime")
            pages = list(
                (
                    await session.execute(
                        select(Page).where(Page.document_id == document.id).order_by(Page.page_number)
                    )
                ).scalars().all()
            )
            extractions = list(
                (
                    await session.execute(
                        select(Extraction).where(Extraction.document_id == document.id)
                    )
                ).scalars().all()
            )

            assert processed.auto_category == "ALM"
            assert processed.user_category == "ALM"
            assert processed.processing_status == "extracted"
            assert processed.total_pages == 2
            assert len(pages) == 2
            assert all(page.parser_used in {"native_table", "native_text", "skip"} for page in pages)
            assert any(extraction.schema_field_key == "lcr_ratio" and extraction.value == "151.7%" for extraction in extractions)
            assert case.status == "extracted"

        await engine.dispose()

    asyncio.run(_run())


def test_process_document_docling_remote_persists_pages_and_extractions(tmp_path, monkeypatch) -> None:
    async def _run() -> None:
        db_path = tmp_path / "app.db"
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        storage_root = tmp_path / "storage"
        storage_root.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(storage, "root", storage_root)

        relative_path = "cases/case-remote/documents/doc-remote/portfolio.csv"
        absolute_path = storage.absolute_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text("metric,value\nGNPA,1.8%\n", encoding="utf-8")

        class FakeRemoteBackend:
            async def convert(self, source_path: Path):
                return type(
                    "RemoteResult",
                    (),
                    {
                        "payload": {
                            "pages": [
                                    {
                                        "page_number": 1,
                                        "text": "Statement of Profit and Loss\nGross NPA 1.8%",
                                        "markdown": "Statement of Profit and Loss\n\nGross NPA 1.8%",
                                        "tables": [
                                            {
                                                "bbox": [0.1, 0.2, 0.5, 0.3],
                                                "rows": [["Metric", "Value"], ["GNPA", "1.8%"]],
                                                "markdown": "| Metric | Value |\n| --- | --- |\n| GNPA | 1.8% |",
                                            }
                                        ],
                                        "bounding_boxes": [
                                            {"text": "Gross NPA 1.8%", "bbox": [0.1, 0.2, 0.5, 0.3]},
                                        ],
                                    }
                            ]
                        },
                        "markdown": "Statement of Profit and Loss\n\nGross NPA 1.8%",
                        "convert_seconds": 1.25,
                    },
                )()

        async def fake_classify_document(*args, **kwargs):
            return ClassificationResult(
                category="Portfolio_Performance",
                confidence=0.91,
                reasoning="test",
            )

        async def fake_extract_with_schema(*args, **kwargs):
            return [
                ExtractionResult(
                    key="gnpa_percent",
                    label="GNPA %",
                    value="1.8%",
                    value_type="percentage",
                    value_numeric=None,
                    page_number=1,
                    confidence=0.88,
                    bbox=(0.1, 0.2, 0.5, 0.3),
                    extraction_method="heuristic_text",
                    extraction_note=None,
                    sheet_name="Performance",
                    row_label="GNPA",
                    column_header="Value",
                    cell_reference="B2",
                )
            ]

        monkeypatch.setattr(
            "backend.app.services.document_pipeline.get_docling_remote_backend",
            lambda: FakeRemoteBackend(),
        )
        monkeypatch.setattr(
            "backend.app.services.document_pipeline.classify_document",
            fake_classify_document,
        )
        monkeypatch.setattr(
            "backend.app.services.document_pipeline.extract_with_schema",
            fake_extract_with_schema,
        )

        async with session_factory() as session:
            case = Case(id="case-remote", company_name="Remote Demo Co", sector="NBFC")
            document = Document(
                id="doc-remote",
                case_id=case.id,
                original_filename="file 01.csv",
                stored_path=relative_path,
                processing_status="pending",
                classification_status="pending",
            )
            session.add(case)
            session.add(document)
            await session.commit()
            await session.refresh(case)
            await session.refresh(document)

            processed = await process_document(session, case, document, backend="docling_remote")
            pages = list(
                (
                    await session.execute(
                        select(Page).where(Page.document_id == document.id).order_by(Page.page_number)
                    )
                ).scalars().all()
            )
            extractions = list(
                (
                    await session.execute(
                        select(Extraction).where(Extraction.document_id == document.id)
                    )
                ).scalars().all()
            )

            assert processed.auto_category == "Portfolio_Performance"
            assert processed.user_category == "Portfolio_Performance"
            assert processed.processing_status == "extracted"
            assert processed.total_pages == 1
            assert len(pages) == 1
            assert pages[0].parser_used == "docling_gpu_remote"
            assert pages[0].content_type == "financial_table"
            assert len(extractions) == 1
            assert extractions[0].schema_field_key == "gnpa_percent"
            assert float(extractions[0].bbox_x1) == 0.1
            assert extractions[0].sheet_name == "Performance"
            assert extractions[0].row_label == "GNPA"
            assert extractions[0].column_header == "Value"
            assert extractions[0].cell_reference == "B2"
            assert case.status == "extracted"

        await engine.dispose()

    asyncio.run(_run())
