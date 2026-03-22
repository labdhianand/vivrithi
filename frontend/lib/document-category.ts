import type { DocumentRecord } from "@/lib/types";

type CompatibleDocumentRecord = DocumentRecord & {
  doc_type?: string | null;
  extraction_status?: string | null;
  processing_status?: string | null;
  status?: string | null;
  failure_reason?: string | null;
  current_stage?: string | null;
  file_size_bytes?: number | null;
  auto_category_confidence?: string | null;
  confidence?: string | null;
};

function asCompatibleDocument(document?: DocumentRecord | null): CompatibleDocumentRecord | null {
  return (document ?? null) as CompatibleDocumentRecord | null;
}

export function getDocumentCategory(document?: DocumentRecord | null): string | null {
  const compatibleDocument = asCompatibleDocument(document);
  return compatibleDocument?.user_category || compatibleDocument?.auto_category || compatibleDocument?.doc_type || null;
}

export function getDocumentExtractionStatus(document?: DocumentRecord | null): string | null {
  return asCompatibleDocument(document)?.extraction_status ?? null;
}

export function getDocumentProcessingStatus(document?: DocumentRecord | null): string | null {
  return asCompatibleDocument(document)?.processing_status ?? null;
}

export function getDocumentLifecycleStatus(document?: DocumentRecord | null): string | null {
  return asCompatibleDocument(document)?.status ?? null;
}

export function getDocumentFailureReason(document?: DocumentRecord | null): string | null {
  return asCompatibleDocument(document)?.failure_reason ?? null;
}

export function getDocumentCurrentStage(document?: DocumentRecord | null): string | null {
  return asCompatibleDocument(document)?.current_stage ?? null;
}

export function getDocumentFileSize(document?: DocumentRecord | null): number | null {
  return asCompatibleDocument(document)?.file_size_bytes ?? null;
}

export function getDocumentConfidence(document?: DocumentRecord | null): string | null {
  const compatibleDocument = asCompatibleDocument(document);
  return compatibleDocument?.auto_category_confidence || compatibleDocument?.confidence || null;
}
