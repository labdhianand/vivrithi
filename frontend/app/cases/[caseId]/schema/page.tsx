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

export default function SchemaPage({ params }: { params: { caseId: string } }) {
  const [schemas, setSchemas] = useState<SchemaRecord[]>([]);
  const [schemaPreviews, setSchemaPreviews] = useState<
    Record<string, { document: DocumentRecord; extractionMap: Record<string, ExtractionRecord> }>
  >({});

  async function refresh() {
    const [documents, existingSchemas] = await Promise.all([listDocuments(params.caseId), listSchemas(params.caseId)]);
    const known = new Map(existingSchemas.map((item) => [item.document_category, item]));
    const categories = Array.from(
      new Set(
        documents
          .map((item) => item.user_category || item.auto_category)
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
      const category = document.user_category || document.auto_category;
      if (!category || document.processing_status !== "extracted") {
        continue;
      }
      const current = latestDocsByCategory.get(category);
      if (!current || new Date(document.updated_at) > new Date(current.updated_at)) {
        latestDocsByCategory.set(category, document);
      }
    }

    const previewEntries = await Promise.all(
      Array.from(latestDocsByCategory.entries()).map(async ([category, document]) => {
        const extractions = await listExtractions(document.id);
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
  }

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Schema Configuration</h1>
        <p className="mt-1 text-slate-500">Review default fields, refine the extraction schema, rerun parsing, and edit extracted values inline.</p>
      </div>

      <div className="space-y-6">
        {schemas.map((schema) => {
          const preview = schemaPreviews[schema.document_category];
          return (
            <SchemaEditor
              key={`${schema.document_category}-${schema.id}`}
              category={schema.document_category}
              initialFields={schema.fields as SchemaField[]}
              extractionPreview={preview?.extractionMap}
              previewDocumentName={preview?.document.original_filename ?? null}
              previewDocumentId={preview?.document.id ?? null}
              onRunExtraction={preview?.document ? async () => {
                await rerunExtraction(preview.document.id);
                await refresh();
              } : undefined}
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
                if (schema.id.length === 36) {
                  await updateSchema(params.caseId, schema.id, payload);
                } else {
                  await saveSchema(params.caseId, payload);
                }
                await refresh();
              }}
            />
          );
        })}

        {schemas.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">
            Upload and classify documents to generate editable schemas.
          </div>
        ) : null}
      </div>
    </div>
  );
}
