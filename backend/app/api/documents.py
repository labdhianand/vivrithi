from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import fitz
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import SessionLocal, get_session
from ..models.case import Case
from ..models.document import Document
from ..models.page import Page
from ..schemas.document import DocumentClassificationUpdate, DocumentPageRead, DocumentProcessRead, DocumentRead
from ..services.document_pipeline import process_document
from ..services.runtime import (
    DocumentArtifact,
    build_docling_artifact,
    build_docling_remote_artifact,
    build_fast_artifact,
    render_overlay_pdf,
)
from ..services.storage import storage


router = APIRouter()
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
}
ARTIFACT_BACKENDS = {
    "fast_runtime",
    "marker",
    "marker_api",
    "marker_remote",
    "docling",
    "docling_remote",
    "docling_gpu",
    "docling_gpu_remote",
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


def _normalize_process_backend(backend: str | None) -> str:
    selected = (backend or get_settings().document_processing_backend).strip().lower()
    if selected not in PROCESS_BACKENDS:
        raise HTTPException(status_code=400, detail=f"Unsupported backend: {selected}")
    if selected == "fast":
        return "fast_runtime"
    if selected in {"marker", "marker_api"}:
        return "marker_remote"
    if selected in {"docling", "docling_remote", "docling_gpu", "docling_gpu_remote"}:
        return "marker_remote"
    return selected


def _normalize_artifact_backend(backend: str | None) -> str:
    selected = (backend or get_settings().document_processing_backend).strip().lower()
    if selected == "fast":
        selected = "fast_runtime"
    if selected in {"marker", "marker_api"}:
        selected = "marker_remote"
    if selected in {"docling_gpu", "docling_gpu_remote", "docling_remote"}:
        selected = "docling_remote"
    if selected not in ARTIFACT_BACKENDS:
        raise HTTPException(status_code=400, detail=f"Unsupported artifact backend: {selected}")
    return selected


async def _build_document_artifact(document: Document, backend: str) -> DocumentArtifact:
    source_path = storage.absolute_path(document.stored_path)
    category = document.user_category or document.auto_category
    if backend == "docling":
        return build_docling_artifact(source_path)
    if backend in {"docling_remote", "marker_remote"}:
        return await build_docling_remote_artifact(source_path)
    return await build_fast_artifact(
        source_path,
        category=category,
        max_workers=get_settings().document_processing_max_workers,
    )


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
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    case = await session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    selected_backend = _normalize_process_backend(get_settings().document_processing_backend)
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
            processing_status="queued",
        )
        session.add(document)
        documents.append(document)

    case.status = "documents_uploaded"
    await session.commit()
    for document in documents:
        await session.refresh(document)
    _enqueue_case_processing(case_id, [document.id for document in documents], selected_backend)
    return documents


async def _process_document_task(case_id: str, document_id: str, backend: str) -> None:
    async with SessionLocal() as task_session:
        case = await task_session.get(Case, case_id)
        document = await task_session.get(Document, document_id)
        if case is None or document is None:
            raise RuntimeError(f"Missing case/document for processing: {case_id}/{document_id}")
        try:
            await process_document(task_session, case, document, backend=backend)
        except Exception as exc:
            document.processing_status = "failed"
            document.failure_reason = str(exc)[:1000] or "Processing failed"
            await task_session.commit()
            raise


async def _run_case_processing(case_id: str, document_ids: list[str], backend: str) -> None:
    semaphore = asyncio.Semaphore(get_settings().document_batch_max_concurrency)

    async def _run(document_id: str) -> None:
        async with semaphore:
            await _process_document_task(case_id, document_id, backend)

    try:
        await asyncio.gather(*[_run(document_id) for document_id in document_ids], return_exceptions=False)
    finally:
        _case_processing_tasks.pop(case_id, None)


def _observe_background_task(task: asyncio.Task[None]) -> None:
    try:
        task.result()
    except Exception:
        return


def _enqueue_case_processing(case_id: str, document_ids: list[str], backend: str) -> None:
    if case_id in _case_processing_tasks and not _case_processing_tasks[case_id].done():
        return
    task = asyncio.create_task(_run_case_processing(case_id, document_ids, backend))
    task.add_done_callback(_observe_background_task)
    _case_processing_tasks[case_id] = task


def _case_processing_active(case_id: str) -> bool:
    return case_id in _case_processing_tasks and not _case_processing_tasks[case_id].done()


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
        processed = await process_document(session, case, document, backend=_normalize_process_backend(backend))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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
            processed = await process_document(session, case, document, backend=selected_backend)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return DocumentProcessRead(document=processed, message="Document retried successfully")
    if _case_processing_active(case.id):
        raise HTTPException(status_code=409, detail="Case processing already in progress")
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

    if wait:
        try:
            await _run_case_processing(case_id, document_ids, selected_backend)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to process one or more documents: {exc}") from exc
    else:
        if not _case_processing_active(case_id):
            for item in documents:
                if item.processing_status not in {"extracted", "completed"}:
                    item.processing_status = "queued"
                    item.failure_reason = None
            await session.commit()
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
    if _case_processing_active(case_id):
        raise HTTPException(status_code=409, detail="Case processing already in progress")
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
    return PlainTextResponse(document.raw_markdown or "")
