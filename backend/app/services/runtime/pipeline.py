from __future__ import annotations

from collections import Counter
from pathlib import Path
from time import perf_counter

from ...extraction_schemas import DEFAULT_SCHEMAS
from ..classifier import classify_document
from ..extractor import extract_with_schema
from ..markdown_builder import build_document_markdown
from .candidates import select_candidate_pages
from .native import parse_document_native
from .types import (
    FastExtractionArtifact,
    FastPageParse,
    FastPipelineResult,
    FieldResolutionTrace,
)


def _field_has_value(item) -> bool:
    return item.value not in (None, "", "[]")


def _required_keys(schema: dict) -> set[str]:
    return {field["key"] for field in schema["fields"] if field.get("required")}


def _merge_results(primary: list, fallback: list) -> list:
    fallback_map = {item.key: item for item in fallback}
    merged = []
    for item in primary:
        fallback_item = fallback_map.get(item.key)
        if not _field_has_value(item) and fallback_item and _field_has_value(fallback_item):
            merged.append(fallback_item)
        else:
            merged.append(item)
    seen = {item.key for item in merged}
    for item in fallback:
        if item.key not in seen:
            merged.append(item)
    return merged


class FastDocumentPipeline:
    def __init__(self, max_workers: int = 8, full_doc_fallback_threshold: int = 4) -> None:
        self.max_workers = max_workers
        self.full_doc_fallback_threshold = full_doc_fallback_threshold

    async def _classify(
        self,
        pdf_path: Path,
        pages: list[FastPageParse],
        forced_category: str | None = None,
    ) -> tuple[str, float]:
        if forced_category:
            return forced_category, 1.0
        first_pages_markdown = "\n\n".join(page.markdown for page in pages[:3])
        page_signal_counts = Counter(page.content_type for page in pages[:5])
        classification = await classify_document(
            first_pages_markdown,
            filename=pdf_path.name,
            page_signal_counts=dict(page_signal_counts),
        )
        return classification.category, classification.confidence

    async def _extract(self, pdf_path: Path, schema: dict, pages: list[FastPageParse]):
        parsed_pages = [page.to_parsed_page() for page in pages]
        return await extract_with_schema(
            pdf_path=pdf_path,
            document_markdown=build_document_markdown(parsed_pages),
            schema=schema,
            pages=parsed_pages,
        )

    async def run(self, pdf_path: Path, forced_category: str | None = None) -> FastPipelineResult:
        return await self.run_with_options(pdf_path, forced_category=forced_category, extraction_category=None)

    async def run_with_options(
        self,
        pdf_path: Path,
        *,
        forced_category: str | None = None,
        extraction_category: str | None = None,
    ) -> FastPipelineResult:
        document = parse_document_native(pdf_path, max_workers=self.max_workers)
        classification_category, classification_confidence = await self._classify(
            pdf_path,
            document.pages,
            forced_category=forced_category,
        )
        schema_category = extraction_category or classification_category
        schema = DEFAULT_SCHEMAS[schema_category]
        candidate_map, candidate_pages = select_candidate_pages(schema, document.pages)

        extraction_started = perf_counter()
        candidate_results = await self._extract(pdf_path, schema, candidate_pages)
        traces: list[FieldResolutionTrace] = []
        result_map = {item.key: item for item in candidate_results}
        required_keys = _required_keys(schema)
        missing_required = [key for key in required_keys if not _field_has_value(result_map.get(key))]
        missing_total = [field["key"] for field in schema["fields"] if not _field_has_value(result_map.get(field["key"]))]

        fallback_results = []
        used_fallback = bool(missing_required) or len(missing_total) >= self.full_doc_fallback_threshold
        if used_fallback and len(candidate_pages) < len(document.pages):
            fallback_results = await self._extract(pdf_path, schema, document.pages)
            merged_results = _merge_results(candidate_results, fallback_results)
            fallback_map = {item.key: item for item in fallback_results}
        else:
            merged_results = candidate_results
            fallback_map = {}

        for field in schema["fields"]:
            candidate_selection = candidate_map[field["key"]]
            final_item = next((item for item in merged_results if item.key == field["key"]), None)
            attempts = ["candidate_select", "candidate_extract"]
            final_method = final_item.extraction_method if final_item else "missing"
            if field["key"] in fallback_map and final_item == fallback_map[field["key"]]:
                attempts.append("full_document_extract")
            traces.append(
                FieldResolutionTrace(
                    field_key=field["key"],
                    selected_pages=candidate_selection.page_numbers,
                    attempts=attempts,
                    resolved=bool(final_item and _field_has_value(final_item)),
                    final_method=final_method,
                )
            )

        field_fill_count = sum(1 for item in merged_results if _field_has_value(item))
        extraction_artifact = FastExtractionArtifact(
            schema_category=schema["category"],
            extraction_results=merged_results,
            candidate_pages=candidate_pages,
            candidate_map=candidate_map,
            resolution_traces=traces,
            extraction_seconds=perf_counter() - extraction_started,
            field_fill_count=field_fill_count,
        )
        return FastPipelineResult(
            document=document,
            classification_category=classification_category,
            classification_confidence=classification_confidence,
            extraction=extraction_artifact,
        )
