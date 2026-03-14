from __future__ import annotations

from fastapi import APIRouter

from .analysis import router as analysis_router
from .cases import router as cases_router
from .documents import router as documents_router
from .extraction import router as extraction_router
from .notes import router as notes_router
from .reports import router as reports_router
from .research import router as research_router
from .schemas import router as schemas_router


router = APIRouter()
router.include_router(cases_router, prefix="/cases", tags=["cases"])
router.include_router(documents_router, tags=["documents"])
router.include_router(extraction_router, tags=["extractions"])
router.include_router(schemas_router, tags=["schemas"])
router.include_router(research_router, tags=["research"])
router.include_router(notes_router, tags=["notes"])
router.include_router(analysis_router, tags=["analysis"])
router.include_router(reports_router, tags=["reports"])

