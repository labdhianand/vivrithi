import type { DocumentRecord } from "@/lib/types";

type LegacyDocumentRecord = DocumentRecord & {
  doc_type?: string | null;
};

export function getDocumentCategory(document?: DocumentRecord | null): string | null {
  if (!document) {
    return null;
  }

  const legacyDocument = document as LegacyDocumentRecord;
  return legacyDocument.user_category || legacyDocument.auto_category || legacyDocument.doc_type || null;
}
