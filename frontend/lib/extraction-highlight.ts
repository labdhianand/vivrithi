import type { ExtractionRecord, SelectedExtractionField } from "@/lib/types";

export function getExtractionFieldLabel(extraction: ExtractionRecord) {
  return extraction.field_label || extraction.schema_field_key;
}

export function toSelectedExtractionField(extraction: ExtractionRecord): SelectedExtractionField | null {
  const page = extraction.bbox?.page || extraction.source_page_number;
  if (!page) {
    return null;
  }
  return {
    extractionId: extraction.id,
    fieldName: getExtractionFieldLabel(extraction),
    page,
    bbox: extraction.bbox || null,
  };
}

export function hasExtractionBBox(extraction: ExtractionRecord) {
  return Boolean(extraction.bbox);
}
