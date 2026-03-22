"use client";

import { useEffect, useState } from "react";

import {
  getDefaultSchema,
  listDocuments,
  listExtractions,
  listSchemas,
  rerunExtraction,
  saveSchema,
  updateExtraction,
  updateSchema,
} from "@/lib/api";
import type { DocumentRecord, ExtractionRecord, SchemaField, SchemaRecord } from "@/lib/types";
import { SchemaEditor } from "@/components/schema/schema-editor";
import { Badge } from "@/components/ui/badge";

type SchemaPreview = {
  document: DocumentRecord;
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
  const [schemaPreviews, setSchemaPreviews] = useState<Record<string, SchemaPreview>>({});
  const [hasProcessingDocuments, setHasProcessingDocuments] = useState(false);

  async function refresh() {
    const [documents, existingSchemas] = await Promise.all([listDocuments(params.caseId), listSchemas(params.caseId)]);
    const known = new Map(existingSchemas.map((item) => [item.document_category, item]));
    const categories = Array.from(
      new Set(
        documents
          .map((item) => item.user_category || item.auto_category || item.doc_type)
          .filter((value): value is string => Boolean(value)),
      ),
    );

    const missing: SchemaRecord[] = [];
    for (const category of categories) {
      if (!known.has(category)) {
        const fallback = await getDefaultSchema(category);
        missing.push({
          id: category,
          case_id: params.caseId,
          document_category: fallback.document_category,
          schema_version: fallback.schema_version,
          fields: fallback.fields,
          is_default: fallback.is_default,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }
    }

    setSchemas([...existingSchemas, ...missing]);

    const latestDocsByCategory = new Map<string, DocumentRecord>();
    for (const document of documents) {
      const category = document.user_category || document.auto_category || document.doc_type;
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
        const extractions = await listExtractions(document.id).catch(() => []);
        return [
          category,
          {
            document,
            extractionMap: Object.fromEntries(extractions.map((entry) => [entry.schema_field_key, entry])),
          },
        ] as const;
      }),
    );

    setSchemaPreviews(Object.fromEntries(previewEntries));

    setHasProcessingDocuments(documents.some((document) => document.extraction_status === "processing"));
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
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fce4ec]">Schema Configuration</h1>
        <p className="mt-1 text-[#ad6883]">
          Review default fields, refine the extraction schema, rerun parsing, and edit extracted values inline.
        </p>
      </div>

      <div className="space-y-6">
        {schemas.map((schema) => {
          const preview = schemaPreviews[schema.document_category];
          const extractionStatus = preview?.document.extraction_status || "pending";

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
                  Full document still processing - schema available but some fields may show Not found.
                </div>
              ) : null}

              {extractionStatus === "extraction_failed" ? (
                <div className="rounded-xl border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300">
                  Background extraction completed partially. Schema is still usable, but some fields may need manual entry.
                </div>
              ) : null}

              <SchemaEditor
                schemaId={schema.id}
                category={schema.document_category}
                initialFields={schema.fields as SchemaField[]}
                extractionPreview={preview?.extractionMap}
                previewDocumentName={preview?.document.original_filename ?? null}
                previewDocumentId={preview?.document.id ?? null}
                onRunExtraction={
                  preview?.document
                    ? async () => {
                        await rerunExtraction(preview.document.id);
                        await refresh();
                      }
                    : undefined
                }
                onUpdateExtraction={async (extractionId, value) => {
                  await updateExtraction(extractionId, { user_edited_value: value, user_verified: true });
                  await refresh();
                }}
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
