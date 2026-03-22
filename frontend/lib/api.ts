import type {
  AnalystNote,
  AnalystNoteInterpretation,
  AnalysisSummary,
  CaseRecord,
  CrossCheck,
  DiscoveredSchemaField,
  DocumentRecord,
  EvidenceRef,
  ExtractionRecord,
  FiveCs,
  PageRecord,
  Recommendation,
  ReportRecord,
  ResearchItem,
  SchemaField,
  SchemaRecord,
  SWOT,
  DocumentExtractionStatusRecord,
} from "@/lib/types";

type LegacyExtractionCandidate = {
  id: string;
  extraction_id: string;
  field_key: string;
  was_selected: boolean;
  value?: string | null;
  confidence?: string | null;
  [key: string]: unknown;
};

const SERVER_API_BASE = (
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8100"
).replace(/\/$/, "");

function buildApiUrl(path: string): string {
  return typeof window === "undefined" ? `${SERVER_API_BASE}${path}` : path;
}

function toNumericValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function normalizeExtraction(record: ExtractionRecord): ExtractionRecord {
  if (record.bbox) {
    return record;
  }
  const page = typeof record.source_page_number === "number" ? record.source_page_number : null;
  const x1 = toNumericValue(record.bbox_x1);
  const y1 = toNumericValue(record.bbox_y1);
  const x2 = toNumericValue(record.bbox_x2);
  const y2 = toNumericValue(record.bbox_y2);
  if (page === null || x1 === null || y1 === null || x2 === null || y2 === null) {
    return { ...record, bbox: null };
  }
  return {
    ...record,
    bbox: {
      page,
      x: x1,
      y: y1,
      width: Math.max(0, x2 - x1),
      height: Math.max(0, y2 - y1),
    },
  };
}

function normalizeExtractions(records: ExtractionRecord[]) {
  return records.map(normalizeExtraction);
}

function parseErrorMessage(message: string, status: number): string {
  if (!message) {
    return `Request failed: ${status}`;
  }
  try {
    const parsed = JSON.parse(message) as { detail?: string };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail;
    }
  } catch {
    // Ignore invalid JSON and use the raw message.
  }
  return message;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response: Response;
  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : "Network request failed");
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(parseErrorMessage(message, response.status));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function listCases() {
  return request<CaseRecord[]>("/api/cases");
}

export async function getCase(caseId: string) {
  return request<CaseRecord>(`/api/cases/${caseId}`);
}

export async function createCase(payload: Partial<CaseRecord>) {
  return request<CaseRecord>("/api/cases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateCase(caseId: string, payload: Partial<CaseRecord>) {
  return request<CaseRecord>(`/api/cases/${caseId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function uploadDocuments(caseId: string, files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  return request<DocumentRecord[]>(`/api/cases/${caseId}/documents/upload`, {
    method: "POST",
    body: form,
    headers: {},
  });
}

export async function listDocuments(caseId: string) {
  return request<DocumentRecord[]>(`/api/cases/${caseId}/documents`);
}

export async function getDocument(documentId: string) {
  return request<DocumentRecord>(`/api/documents/${documentId}`);
}

export async function getDocumentExtractionStatus(documentId: string) {
  return request<DocumentExtractionStatusRecord>(`/api/documents/${documentId}/extraction-status`);
}

export async function deleteDocument(docId: string) {
  return request<void>(`/api/documents/${docId}`, {
    method: "DELETE",
  });
}

export async function updateDocumentClassification(
  documentId: string,
  payload: { user_category: string; classification_status: string },
) {
  return request<DocumentRecord>(`/api/documents/${documentId}/classify`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function approveClassification(documentId: string, category: string) {
  return updateDocumentClassification(documentId, {
    user_category: category,
    classification_status: "user_approved",
  });
}

export async function rejectClassification(documentId: string) {
  return updateDocumentClassification(documentId, {
    user_category: "",
    classification_status: "rejected",
  });
}

export async function processDocument(documentId: string) {
  return request<{ document: DocumentRecord; message: string }>(`/api/documents/${documentId}/process`, {
    method: "POST",
  });
}

export async function processCaseDocuments(caseId: string) {
  return request<DocumentRecord[]>(`/api/cases/${caseId}/documents/process`, {
    method: "POST",
  });
}

export async function listPages(documentId: string) {
  return request<PageRecord[]>(`/api/documents/${documentId}/pages`);
}

export async function listExtractions(documentId: string) {
  return normalizeExtractions(await request<ExtractionRecord[]>(`/api/documents/${documentId}/extractions`));
}

export async function listCandidates(..._args: unknown[]): Promise<LegacyExtractionCandidate[]> {
  // Compatibility shim for stale client code paths that still import candidate APIs.
  return [];
}

export async function selectCandidate(..._args: unknown[]): Promise<LegacyExtractionCandidate | null> {
  return null;
}

export async function updateExtraction(extractionId: string, payload: Partial<ExtractionRecord>) {
  return normalizeExtraction(await request<ExtractionRecord>(`/api/extractions/${extractionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }));
}

export async function rerunExtraction(documentId: string) {
  return normalizeExtractions(await request<ExtractionRecord[]>(`/api/documents/${documentId}/extract`, {
    method: "POST",
  }));
}

export async function discoverExtractionFields(documentId: string) {
  return request<DiscoveredSchemaField[]>(`/api/extraction/${documentId}/discover`, {
    method: "POST",
  });
}

export async function getDefaultSchema(category: string) {
  return request<{ document_category: string; fields: SchemaField[]; schema_version: number; is_default: boolean }>(
    `/api/schemas/defaults/${category}`,
  );
}

export async function listSchemas(caseId: string) {
  return request<SchemaRecord[]>(`/api/cases/${caseId}/schemas`);
}

export async function saveSchema(caseId: string, payload: { document_category: string; fields: SchemaField[]; schema_version: number; is_default: boolean }) {
  return request<SchemaRecord>(`/api/cases/${caseId}/schemas`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateSchema(caseId: string, schemaId: string, payload: { document_category: string; fields: SchemaField[]; schema_version: number; is_default: boolean }) {
  return request<SchemaRecord>(`/api/cases/${caseId}/schemas/${schemaId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function runResearch(caseId: string) {
  return request<ResearchItem[]>(`/api/cases/${caseId}/research/run`, { method: "POST" });
}

export async function listResearch(caseId: string) {
  return request<ResearchItem[]>(`/api/cases/${caseId}/research`);
}

export async function deleteResearchItem(itemId: string) {
  return request<{ message: string }>(`/api/research/${itemId}`, { method: "DELETE" });
}

export async function createNote(caseId: string, payload: Partial<AnalystNote>) {
  return request<AnalystNote>(`/api/cases/${caseId}/notes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function interpretNote(caseId: string, payload: { note_type?: string | null; content: string }) {
  return request<AnalystNoteInterpretation>(`/api/cases/${caseId}/notes/interpret`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function previewNoteImpact(...args: unknown[]) {
  const [caseId, payload] = args as [string | undefined, { note_type?: string | null; content?: string } | undefined];
  if (typeof caseId !== "string" || !payload || typeof payload.content !== "string") {
    throw new Error("previewNoteImpact requires a caseId and note content");
  }
  return interpretNote(caseId, {
    note_type: payload.note_type ?? null,
    content: payload.content,
  });
}

export async function listNotes(caseId: string) {
  return request<AnalystNote[]>(`/api/cases/${caseId}/notes`);
}

export async function deleteNote(noteId: string) {
  return request<{ message: string }>(`/api/notes/${noteId}`, { method: "DELETE" });
}

export async function runAnalysis(caseId: string) {
  return request<Recommendation>(`/api/cases/${caseId}/analyze`, { method: "POST" });
}

export async function getCrossChecks(caseId: string) {
  return request<CrossCheck[]>(`/api/cases/${caseId}/cross-verification`);
}

export async function getFiveCs(caseId: string) {
  return request<FiveCs>(`/api/cases/${caseId}/five-cs`);
}

export async function getRecommendation(caseId: string) {
  return request<Recommendation>(`/api/cases/${caseId}/recommendation`);
}

export async function getSwot(caseId: string) {
  return request<SWOT>(`/api/cases/${caseId}/swot`);
}

export async function getAnalysisSummary(caseId: string) {
  return request<AnalysisSummary>(`/api/cases/${caseId}/analysis-summary`);
}

export async function generateReport(caseId: string) {
  return request<ReportRecord>(`/api/cases/${caseId}/reports/generate`, { method: "POST" });
}

export async function listReports(caseId: string) {
  return request<ReportRecord[]>(`/api/cases/${caseId}/reports`);
}

export async function getReportPreview(reportId: string) {
  return request<{ report: ReportRecord; sections: Array<{ id: string; title: string; content_markdown: string; evidence_refs?: EvidenceRef[] }> }>(
    `/api/reports/${reportId}/preview`,
  );
}

export function getPageImageUrl(documentId: string, pageNumber: number) {
  return `/api/documents/${documentId}/pages/${pageNumber}/image`;
}

export function getReportDownloadUrl(reportId: string, format: "docx" | "pdf") {
  return `/api/reports/${reportId}/download/${format}`;
}
