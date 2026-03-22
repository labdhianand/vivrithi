"use client";

import { useEffect, useState } from "react";

import {
  getDefaultSchema,
  listDocuments,
  listExtractions,
  listPages,
  listSchemas,
  rerunExtraction,
  saveSchema,
  updateExtraction,
  updateSchema,
} from "@/lib/api";
import { toSelectedExtractionField } from "@/lib/extraction-highlight";
import { getDocumentCategory, getDocumentExtractionStatus } from "@/lib/document-category";
import type {
  DocumentRecord,
  ExtractionRecord,
  PageRecord,
  SchemaField,
  SchemaRecord,
  SelectedExtractionField,
} from "@/lib/types";
import { ExtractedDataTable } from "@/components/extraction/extracted-data-table";
import { PdfViewer } from "@/components/extraction/pdf-viewer";
import { SchemaEditor } from "@/components/schema/schema-editor";
import { Badge } from "@/components/ui/badge";

type SchemaPreview = {
  document: DocumentRecord;
  pages: PageRecord[];
  extractions: ExtractionRecord[];
  extractionMap: Record<string, ExtractionRecord>;
};

function extractionTone(status: string): "success" | "warn" | "danger" | "neutral" {
  switch (status) {
    case "extracted":
      return "success";
    case "processing":
      return "warn";
    case "extraction_failed":
      return "danger";
    default:
      return "neutral";
  }
}

function extractionLabel(status: string) {
  switch (status) {
    case "extracted":
      return "Ready";
    case "processing":
      return "Extracting...";
    case "extraction_failed":
      return "Partial";
    default:
      return "Pending";
  }
}

export default function SchemaPage({ params }: { params: { caseId: string } }) {
  const [schemas, setSchemas] = useState<SchemaRecord[]>([]);
  const [schemaDefaults, setSchemaDefaults] = useState<Record<string, SchemaField[]>>({});
  const [schemaPreviews, setSchemaPreviews] = useState<Record<string, SchemaPreview>>({});
  const [hasProcessingDocuments, setHasProcessingDocuments] = useState(false);
  const [activePages, setActivePages] = useState<Record<string, number | undefined>>({});
  const [selectedFields, setSelectedFields] = useState<Record<string, SelectedExtractionField | null>>({});

  async function refresh() {
    const [documents, existingSchemas] = await Promise.all([listDocuments(params.caseId), listSchemas(params.caseId)]);
    const categories = Array.from(
      new Set(
        [...existingSchemas.map((schema) => schema.document_category), ...documents.map((document) => getDocumentCategory(document))]
          .filter((value): value is string => Boolean(value)),
      ),
    );

    const defaultSchemaEntries = await Promise.all(
      categories.map(async (category) => {
        const fallback = await getDefaultSchema(category);
        return [category, fallback] as const;
      }),
    );
    const defaultSchemaMap = Object.fromEntries(
      defaultSchemaEntries.map(([category, fallback]) => [category, fallback.fields]),
    );
    setSchemaDefaults(defaultSchemaMap);

    const known = new Map(existingSchemas.map((item) => [item.document_category, item]));
    const missing: SchemaRecord[] = defaultSchemaEntries
      .filter(([category]) => !known.has(category))
      .map(([category, fallback]) => ({
        id: category,
        case_id: params.caseId,
        document_category: fallback.document_category,
        schema_version: fallback.schema_version,
        fields: fallback.fields,
        is_default: fallback.is_default,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

    setSchemas([...existingSchemas, ...missing]);

    const latestDocsByCategory = new Map<string, DocumentRecord>();
    for (const document of documents) {
      const category = getDocumentCategory(document);
      if (!category) {
        continue;
      }
      const current = latestDocsByCategory.get(category);
      if (!current || new Date(document.updated_at) > new Date(current.updated_at)) {
        latestDocsByCategory.set(category, document);
      }
    }

    const previewEntries = await Promise.all(
      Array.from(latestDocsByCategory.entries()).map(async ([category, document]) => {
        const [pages, extractions] = await Promise.all([
          listPages(document.id).catch(() => []),
          listExtractions(document.id).catch(() => []),
        ]);
        return [
          category,
          {
            document,
            pages,
            extractions,
            extractionMap: Object.fromEntries(extractions.map((entry) => [entry.schema_field_key, entry])),
          },
        ] as const;
      }),
    );

    const previews = Object.fromEntries(previewEntries);
    setSchemaPreviews(previews);
    setActivePages((current) => {
      const next = { ...current };
      for (const [category, preview] of Object.entries(previews)) {
        if (next[category] == null && preview.pages[0]?.page_number) {
          next[category] = preview.pages[0].page_number;
        }
      }
      return next;
    });

    setHasProcessingDocuments(documents.some((document) => getDocumentExtractionStatus(document) === "processing"));
  }

  useEffect(() => {
    void refresh();
  }, [params.caseId]);

  useEffect(() => {
    if (!hasProcessingDocuments) {
      return;
    }
    const intervalId = window.setInterval(() => {
      void refresh();
    }, 3000);
    return () => window.clearInterval(intervalId);
  }, [hasProcessingDocuments, params.caseId]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fce4ec]">Schema Configuration</h1>
        <p className="mt-1 text-[#ad6883]">
          Review standard fields, add AI-discovered fields, rerun parsing, and click any extracted field to highlight its source on the PDF preview.
        </p>
      </div>

      <div className="space-y-6">
        {schemas.map((schema) => {
          const preview = schemaPreviews[schema.document_category];
          const extractionStatus = getDocumentExtractionStatus(preview?.document) || "pending";
          const selectedField = selectedFields[schema.document_category] || null;
          const activePage = activePages[schema.document_category] || preview?.pages[0]?.page_number;

          return (
            <div key={`${schema.document_category}-${schema.id}`} className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#4a1530] bg-[#1f0d16] px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-[#fce4ec]">{schema.document_category.replace(/_/g, " ")}</p>
                  {preview?.document ? (
                    <p className="mt-1 text-xs text-[#ad6883]">{preview.document.original_filename}</p>
                  ) : (
                    <p className="mt-1 text-xs text-[#ad6883]">No document uploaded for this category yet.</p>
                  )}
                </div>
                <Badge tone={extractionTone(extractionStatus)} pulse={extractionStatus === "processing"}>
                  {extractionLabel(extractionStatus)}
                </Badge>
              </div>

              {extractionStatus === "processing" ? (
                <div className="rounded-xl border border-amber-800 bg-amber-950 px-4 py-3 text-sm text-amber-300">
                  Full document still processing. Standard fields are editable now and AI discovery will auto-run once extraction completes.
                </div>
              ) : null}

              {extractionStatus === "extraction_failed" ? (
                <div className="rounded-xl border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300">
                  Background extraction completed partially. You can still refine the schema and inspect available evidence.
                </div>
              ) : null}

              <SchemaEditor
                schemaId={schema.id}
                category={schema.document_category}
                initialFields={schema.fields as SchemaField[]}
                standardFields={schemaDefaults[schema.document_category] || (schema.fields as SchemaField[])}
                previewDocumentName={preview?.document.original_filename ?? null}
                previewDocumentId={preview?.document.id ?? null}
                extractionStatus={extractionStatus}
                onRunExtraction={
                  preview?.document
                    ? async () => {
                        await rerunExtraction(preview.document.id);
                        await refresh();
                      }
                    : undefined
                }
                onSave={async (fields) => {
                  const payload = {
                    document_category: schema.document_category,
                    fields,
                    schema_version: schema.schema_version + 1,
                    is_default: false,
                  };
                  const response =
                    schema.id.length === 36
                      ? { data: await updateSchema(params.caseId, schema.id, payload) }
                      : { data: await saveSchema(params.caseId, payload) };
                  setSchemas((current) =>
                    current.map((item) =>
                      item.id === schema.id || item.document_category === response.data.document_category
                        ? response.data
                        : item,
                    ),
                  );
                }}
              />

              {preview?.document ? (
                <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                  <PdfViewer
                    documentId={preview.document.id}
                    document={preview.document}
                    pages={preview.pages}
                    activePage={activePage}
                    extractions={preview.extractions}
                    selectedField={selectedField}
                    onSelectExtraction={(extractionId) => {
                      const extraction = preview.extractions.find((item) => item.id === extractionId);
                      const nextSelection = extraction ? toSelectedExtractionField(extraction) : null;
                      if (!nextSelection) {
                        return;
                      }
                      setSelectedFields((current) => ({ ...current, [schema.document_category]: nextSelection }));
                      setActivePages((current) => ({ ...current, [schema.document_category]: nextSelection.page }));
                    }}
                    onSelectPage={(pageNumber) => {
                      setActivePages((current) => ({ ...current, [schema.document_category]: pageNumber }));
                    }}
                  />
                  <ExtractedDataTable
                    extractions={preview.extractions}
                    selectedExtractionId={selectedField?.extractionId}
                    onSelectField={(field) => {
                      setSelectedFields((current) => ({ ...current, [schema.document_category]: field }));
                      setActivePages((current) => ({ ...current, [schema.document_category]: field.page }));
                    }}
                    onSave={async (extractionId, value) => {
                      await updateExtraction(extractionId, { user_edited_value: value, user_verified: true });
                      await refresh();
                    }}
                  />
                </div>
              ) : null}
            </div>
          );
        })}

        {schemas.length === 0 ? (
          <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-8 text-center text-[#ad6883] shadow-sm">
            Upload and classify documents to generate editable schemas.
          </div>
        ) : null}
      </div>
    </div>
  );
}
