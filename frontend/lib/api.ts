import type {
  AnalystNote,
  CaseRecord,
  CrossCheck,
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
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
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

export async function approveClassification(documentId: string, category: string) {
  return request<DocumentRecord>(`/api/documents/${documentId}/classify`, {
    method: "PATCH",
    body: JSON.stringify({
      user_category: category,
      classification_status: "user_approved",
    }),
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
  return request<ExtractionRecord[]>(`/api/documents/${documentId}/extractions`);
}

export async function updateExtraction(extractionId: string, payload: Partial<ExtractionRecord>) {
  return request<ExtractionRecord>(`/api/extractions/${extractionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function rerunExtraction(documentId: string) {
  return request<ExtractionRecord[]>(`/api/documents/${documentId}/extract`, {
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
  return `${API_BASE}/api/documents/${documentId}/pages/${pageNumber}/image`;
}

export function getReportDownloadUrl(reportId: string, format: "docx" | "pdf") {
  return `${API_BASE}/api/reports/${reportId}/download/${format}`;
}
