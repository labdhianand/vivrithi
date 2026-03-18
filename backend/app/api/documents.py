from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from decimal import Decimal
from pathlib import Path

import fitz
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import SessionLocal, get_session
from ..models.case import Case
from ..models.document import Document
from ..models.page import Page
from ..schemas.document import (
    DocumentClassificationUpdate,
    DocumentExtractionStatusRead,
    DocumentPageRead,
    DocumentProcessRead,
    DocumentRead,
)
from ..services.document_pipeline import (
    classify_uploaded_document,
    extract_document_payload,
    process_document,
)
from ..services.pdf_triage import classify_page_content
from ..services.runtime import (
    DocumentArtifact,
    build_docling_artifact,
    build_docling_remote_artifact,
    render_overlay_pdf,
)
from ..services.storage import storage


router = APIRouter()
logger = logging.getLogger(__name__)
DOCUMENT_PROCESSING_TIMEOUT_SECONDS = 60.0
PROCESS_BACKENDS = {
    "legacy",
    "classic",
    "fast",
    "fast_runtime",
    "marker",
    "marker_api",
    "marker_remote",
    "docling",
    "docling_remote",
    "docling_gpu",
    "docling_gpu_remote",
    "pdfplumber",
}
ARTIFACT_BACKENDS = {
    "docling",
    "docling_remote",
    "docling_gpu",
    "docling_gpu_remote",
    "fast_runtime",
    "marker",
    "marker_api",
    "marker_remote",
    "pdfplumber",
}
SUPPORTED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".xlsx",
    ".xls",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
}
_case_processing_tasks: dict[str, asyncio.Task[None]] = {}
_case_processing_queue: dict[str, list[tuple[str, str]]] = {}
_case_processing_inflight: dict[str, set[str]] = {}


class DocumentProcessingError(RuntimeError):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _background_extraction_timeout_seconds(file_path: str) -> int:
    file_size = os.path.getsize(file_path)
    if file_size > 5_000_000:
        return 300
    if file_size > 2_000_000:
        return 180
    return 120


async def _refresh_case_status(session: AsyncSession, case_id: str) -> None:
    case = await session.get(Case, case_id)
    if case is None:
        return
    result = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    documents = list(result.scalars().all())
    if not documents:
        case.status = "onboarding"
        return
    if any(document.extraction_status == "processing" for document in documents):
        case.status = "extracting"
        return
    if any(document.extraction_status == "extracted" for document in documents):
        case.status = "extracted"
        return
    case.status = "documents_uploaded"


async def _replace_document_pages(
    session: AsyncSession,
    document: Document,
    parsed_pages,
) -> None:
    await session.execute(delete(Page).where(Page.document_id == document.id))
    for parsed_page in parsed_pages:
        has_tables = bool(parsed_page.tables)
        session.add(
            Page(
                document_id=document.id,
                page_number=parsed_page.page_number,
                is_scanned=False,
                has_tables=has_tables,
                content_type=classify_page_content(parsed_page.text, False, has_tables),
                parser_used=parsed_page.parser_used or "marker_api",
                raw_text=parsed_page.text,
                raw_markdown=parsed_page.markdown,
                page_image_path=None,
                parsing_confidence=Decimal(str(round(parsed_page.confidence, 4))),
                parsing_duration_ms=0,
            )
        )


async def run_full_extraction_background(
    doc_id: str,
    file_path: str,
    case_id: str,
) -> None:
    timeout_seconds = _background_extraction_timeout_seconds(file_path)
    try:
        async with SessionLocal() as session:
            document = await session.get(Document, doc_id)
            if document is None:
                return
            document.extraction_status = "processing"
            document.processing_status = "processing"
            document.failure_reason = None
            await _refresh_case_status(session, case_id)
            await session.commit()

        _, payload, parsed_pages = await asyncio.wait_for(
            extract_document_payload(Path(file_path)),
            timeout=timeout_seconds,
        )

        async with SessionLocal() as session:
            document = await session.get(Document, doc_id)
            if document is None:
                return
            document.extracted_text = payload.get("markdown") or payload.get("text") or ""
            document.total_pages = int(payload.get("page_count") or len(parsed_pages))
            document.extraction_status = "extracted"
            document.processing_status = "extracted"
            document.failure_reason = None
            await _replace_document_pages(session, document, parsed_pages)
            await _refresh_case_status(session, case_id)
            await session.commit()
    except Exception as exc:
        logger.exception("Background extraction failed for %s", doc_id)
        async with SessionLocal() as session:
            document = await session.get(Document, doc_id)
            if document is None:
                return
            document.extraction_status = "extraction_failed"
            document.processing_status = "extraction_failed"
            document.failure_reason = str(exc)[:1000] or "Background extraction failed"
            await _refresh_case_status(session, case_id)
            await session.commit()


def _normalize_process_backend(backend: str | None) -> str:
    selected = (backend or get_settings().document_processing_backend or "docling_remote").strip().lower()
    if selected not in PROCESS_BACKENDS:
        raise HTTPException(status_code=400, detail=f"Unsupported backend: {selected}")
    return "docling_remote"


def _normalize_artifact_backend(backend: str | None) -> str:
    selected = (backend or get_settings().document_processing_backend or "docling_remote").strip().lower()
    if selected not in ARTIFACT_BACKENDS:
        raise HTTPException(status_code=400, detail=f"Unsupported artifact backend: {selected}")
    return "docling_remote"


async def _build_document_artifact(document: Document, backend: str) -> DocumentArtifact:
    source_path = storage.absolute_path(document.stored_path)
    if backend == "docling":
        return build_docling_artifact(source_path)
    return await build_docling_remote_artifact(source_path)


async def _mark_document_failed(
    session: AsyncSession,
    document: Document,
    message: str,
) -> None:
    if document.status == "classified":
        document.extraction_status = "extraction_failed"
        document.processing_status = "extraction_failed"
    else:
        document.status = "failed"
        document.processing_status = "failed"
    document.failure_reason = (message or "Processing failed")[:1000]
    await session.commit()


async def _run_document_processing_with_timeout(
    session: AsyncSession,
    case: Case,
    document: Document,
    backend: str,
) -> Document:
    try:
        return await asyncio.wait_for(
            process_document(session, case, document, backend=backend),
            timeout=DOCUMENT_PROCESSING_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        timeout_label = f"{DOCUMENT_PROCESSING_TIMEOUT_SECONDS:g}"
        message = f"Processing timed out after {timeout_label} seconds"
        await _mark_document_failed(session, document, message)
        logger.error("Document %s timed out after %s seconds", document.id, DOCUMENT_PROCESSING_TIMEOUT_SECONDS)
        raise DocumentProcessingError(message, status_code=504) from exc
    except asyncio.CancelledError as exc:
        message = "Processing cancelled before completion"
        await _mark_document_failed(session, document, message)
        logger.warning("Document %s processing was cancelled", document.id)
        raise DocumentProcessingError(message, status_code=500) from exc
    except ValueError as exc:
        message = str(exc)[:1000] or "Invalid processing request"
        await _mark_document_failed(session, document, message)
        logger.error("Document %s failed validation during processing: %s", document.id, message)
        raise DocumentProcessingError(message, status_code=400) from exc
    except Exception as exc:
        message = str(exc)[:1000] or "Processing failed"
        await _mark_document_failed(session, document, message)
        logger.exception("Document %s failed during processing", document.id)
        raise DocumentProcessingError(message, status_code=500) from exc


async def _ensure_page_image(
    session: AsyncSession,
    document: Document,
    page: Page,
    page_num: int,
) -> str:
    if page.page_image_path:
        absolute_path = storage.absolute_path(page.page_image_path)
        if absolute_path.exists():
            return str(absolute_path)
    pdf_path = storage.absolute_path(document.stored_path)
    with fitz.open(pdf_path) as pdf:
        if page_num < 1 or page_num > pdf.page_count:
            raise HTTPException(status_code=404, detail="Page image not found")
        pixmap = pdf[page_num - 1].get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
        relative_path = storage.save_page_image(
            document.case_id,
            document.id,
            page_num,
            pixmap.tobytes("png"),
        )
    page.page_image_path = relative_path
    await session.commit()
    return str(storage.absolute_path(relative_path))


@router.post("/cases/{case_id}/documents/upload", response_model=list[DocumentRead])
async def upload_documents(
    case_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    documents: list[Document] = []
    for upload in files:
        filename = upload.filename or "document"
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")
        document_id = str(uuid.uuid4())
        try:
            stored = await storage.save_upload(case_id, document_id, upload)
        except ValueError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        document = Document(
            id=document_id,
            case_id=case_id,
            original_filename=filename,
            stored_path=stored["relative_path"],
            file_size_bytes=stored["file_size_bytes"],
            mime_type=stored["mime_type"],
            sha256_hash=stored["sha256"],
            status="uploaded",
            processing_status="pending",
            extraction_status="pending",
        )
        session.add(document)
        await session.flush()

        source_path = storage.absolute_path(document.stored_path)
        try:
            classification, first_page_text = await classify_uploaded_document(
                source_path,
                filename=document.original_filename,
            )
        except Exception as exc:
            logger.exception("Upload classification failed for %s", filename)
            document.status = "failed"
            document.processing_status = "failed"
            document.failure_reason = str(exc)[:1000] or "Classification failed"
            await session.commit()
            raise HTTPException(status_code=500, detail=document.failure_reason) from exc

        document.status = "classified"
        document.auto_category = classification.category
        document.auto_category_confidence = Decimal(str(round(classification.confidence, 4)))
        document.classification_reason = classification.reasoning
        document.classification_text = first_page_text
        document.classification_status = "auto_classified"
        document.extraction_status = "processing"
        document.processing_status = "processing"
        document.failure_reason = None
        documents.append(document)
        background_tasks.add_task(
            run_full_extraction_background,
            doc_id=document.id,
            file_path=str(source_path),
            case_id=case_id,
        )

    case.status = "extracting"
    await session.commit()
    for document in documents:
        await session.refresh(document)
    return documents


async def _process_document_task(case_id: str, document_id: str, backend: str) -> None:
    async with SessionLocal() as task_session:
        case = await task_session.get(Case, case_id)
        document = await task_session.get(Document, document_id)
        if case is None or document is None:
            raise RuntimeError(f"Missing case/document for processing: {case_id}/{document_id}")
        try:
            await _run_document_processing_with_timeout(task_session, case, document, backend=backend)
        except DocumentProcessingError:
            return


async def _run_case_processing(case_id: str) -> None:
    semaphore = asyncio.Semaphore(get_settings().document_batch_max_concurrency)
    inflight = _case_processing_inflight.setdefault(case_id, set())

    async def _run(document_id: str, backend: str) -> None:
        inflight.add(document_id)
        try:
            async with semaphore:
                await _process_document_task(case_id, document_id, backend)
        finally:
            inflight.discard(document_id)

    try:
        while True:
            queued_items = _case_processing_queue.get(case_id, [])
            if not queued_items:
                return

            _case_processing_queue[case_id] = []
            await asyncio.gather(
                *[_run(document_id, backend) for document_id, backend in queued_items],
                return_exceptions=False,
            )
    finally:
        _case_processing_inflight.pop(case_id, None)
        _case_processing_tasks.pop(case_id, None)
        if _case_processing_queue.get(case_id):
            next_task = asyncio.create_task(_run_case_processing(case_id))
            next_task.add_done_callback(_observe_background_task)
            _case_processing_tasks[case_id] = next_task
        else:
            _case_processing_queue.pop(case_id, None)


def _observe_background_task(task: asyncio.Task[None]) -> None:
    try:
        task.result()
    except BaseException:
        logger.exception("Background case processing task failed unexpectedly")
        return


def _enqueue_case_processing(case_id: str, document_ids: list[str], backend: str) -> None:
    queue = _case_processing_queue.setdefault(case_id, [])
    inflight = _case_processing_inflight.setdefault(case_id, set())
    queued_ids = {document_id for document_id, _ in queue}

    for document_id in document_ids:
        if document_id in inflight or document_id in queued_ids:
            continue
        queue.append((document_id, backend))
        queued_ids.add(document_id)

    if case_id in _case_processing_tasks and not _case_processing_tasks[case_id].done():
        return

    task = asyncio.create_task(_run_case_processing(case_id))
    task.add_done_callback(_observe_background_task)
    _case_processing_tasks[case_id] = task


@router.get("/cases/{case_id}/documents", response_model=list[DocumentRead])
async def list_case_documents(case_id: str, session: AsyncSession = Depends(get_session)) -> list[Document]:
    result = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    return list(result.scalars().all())


@router.get("/documents/{doc_id}", response_model=DocumentRead)
async def get_document(doc_id: str, session: AsyncSession = Depends(get_session)) -> Document:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/documents/{doc_id}/extraction-status", response_model=DocumentExtractionStatusRead)
async def get_document_extraction_status(
    doc_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentExtractionStatusRead:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentExtractionStatusRead(
        doc_id=document.id,
        extraction_status=document.extraction_status,
        extracted=document.extraction_status == "extracted",
    )


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    document = await session.get(Document, doc_id)
    if not document:
        return Response(status_code=204)
    case_id = document.case_id
    absolute_path = storage.absolute_path(document.stored_path)
    document_dir = absolute_path.parent
    await session.delete(document)
    await session.commit()
    if document_dir.exists():
        shutil.rmtree(document_dir, ignore_errors=True)
    await _refresh_case_status(session, case_id)
    await session.commit()
    return Response(status_code=204)


@router.patch("/documents/{doc_id}/classify", response_model=DocumentRead)
async def update_document_classification(
    doc_id: str,
    payload: DocumentClassificationUpdate,
    session: AsyncSession = Depends(get_session),
) -> Document:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.user_category = payload.user_category
    document.classification_status = payload.classification_status
    await session.commit()
    await session.refresh(document)
    return document


@router.post("/documents/{doc_id}/process", response_model=DocumentProcessRead)
async def process_document_endpoint(
    doc_id: str,
    backend: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> DocumentProcessRead:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    case = await session.get(Case, document.case_id)
    try:
        document.processing_status = "queued"
        document.failure_reason = None
        await session.commit()
        processed = await _run_document_processing_with_timeout(
            session,
            case,
            document,
            backend=_normalize_process_backend(backend),
        )
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return DocumentProcessRead(document=processed, message="Document processed")


@router.post("/documents/{doc_id}/retry", response_model=DocumentProcessRead)
async def retry_document_processing(
    doc_id: str,
    backend: str | None = Query(default=None),
    wait: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> DocumentProcessRead:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    case = await session.get(Case, document.case_id)
    selected_backend = _normalize_process_backend(backend)
    document.processing_status = "queued"
    document.failure_reason = None
    await session.commit()
    await session.refresh(document)
    if wait:
        try:
            processed = await _run_document_processing_with_timeout(session, case, document, backend=selected_backend)
        except DocumentProcessingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        return DocumentProcessRead(document=processed, message="Document retried successfully")
    _enqueue_case_processing(case.id, [document.id], selected_backend)
    await session.refresh(document)
    return DocumentProcessRead(document=document, message="Document retry queued")


@router.post("/cases/{case_id}/documents/process", response_model=list[DocumentRead])
async def process_case_documents(
    case_id: str,
    backend: str | None = Query(default=None),
    wait: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    documents = list(
        (
            await session.execute(
                select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
            )
        ).scalars().all()
    )
    if not documents:
        return []
    selected_backend = _normalize_process_backend(backend)
    document_ids = [item.id for item in documents]
    for item in documents:
        if item.processing_status not in {"extracted", "completed"}:
            item.processing_status = "queued"
            item.failure_reason = None
    await session.commit()

    if wait:
        _enqueue_case_processing(case_id, document_ids, selected_backend)
        active_task = _case_processing_tasks.get(case_id)
        if active_task is not None:
            await active_task
    else:
        _enqueue_case_processing(case_id, document_ids, selected_backend)
    refreshed = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    return list(refreshed.scalars().all())


@router.post("/cases/{case_id}/documents/retry-failed", response_model=list[DocumentRead])
async def retry_failed_case_documents(
    case_id: str,
    backend: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    documents = [item for item in result.scalars().all() if item.processing_status == "failed"]
    if not documents:
        return []
    for item in documents:
        item.processing_status = "queued"
        item.failure_reason = None
    await session.commit()
    _enqueue_case_processing(case_id, [item.id for item in documents], _normalize_process_backend(backend))
    refreshed = await session.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.created_at)
    )
    return list(refreshed.scalars().all())


@router.get("/documents/{doc_id}/pages", response_model=list[DocumentPageRead])
async def list_document_pages(doc_id: str, session: AsyncSession = Depends(get_session)) -> list[Page]:
    result = await session.execute(
        select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
    )
    return list(result.scalars().all())


@router.get("/documents/{doc_id}/pages/{page_num}/image")
async def get_document_page_image(doc_id: str, page_num: int, session: AsyncSession = Depends(get_session)) -> FileResponse:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    result = await session.execute(
        select(Page).where(Page.document_id == doc_id, Page.page_number == page_num)
    )
    page = result.scalars().first()
    if not page:
        raise HTTPException(status_code=404, detail="Page image not found")
    absolute_path = await _ensure_page_image(session, document, page, page_num)
    return FileResponse(absolute_path)


@router.get("/documents/{doc_id}/artifact")
async def get_document_artifact(
    doc_id: str,
    backend: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    artifact = await _build_document_artifact(document, _normalize_artifact_backend(backend))
    return JSONResponse(content=artifact.to_dict())


@router.get("/documents/{doc_id}/overlay")
async def get_document_overlay(
    doc_id: str,
    backend: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    normalized_backend = _normalize_artifact_backend(backend)
    artifact = await _build_document_artifact(document, normalized_backend)
    pdf_path = storage.absolute_path(document.stored_path)
    overlay_relative_path = (
        f"cases/{document.case_id}/documents/{document.id}/artifacts/{normalized_backend}_overlay.pdf"
    )
    overlay_absolute_path = storage.absolute_path(overlay_relative_path)
    render_overlay_pdf(pdf_path, artifact, overlay_absolute_path)
    return FileResponse(overlay_absolute_path, filename=f"{doc_id}-{normalized_backend}-overlay.pdf")


@router.get("/documents/{doc_id}/markdown")
async def get_document_markdown(doc_id: str, session: AsyncSession = Depends(get_session)) -> PlainTextResponse:
    document = await session.get(Document, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(document.extracted_text or document.raw_markdown or "")
