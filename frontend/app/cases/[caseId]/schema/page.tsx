"use client";

import { useEffect, useState } from "react";

import { getDefaultSchema, listDocuments, listExtractions, listSchemas, saveSchema, updateSchema } from "@/lib/api";
import type { DocumentRecord, ExtractionRecord, SchemaField, SchemaRecord } from "@/lib/types";
import { SchemaEditor } from "@/components/schema/schema-editor";
import { Badge } from "@/components/ui/badge";

export default function SchemaPage({ params }: { params: { caseId: string } }) {
  const [schemas, setSchemas] = useState<SchemaRecord[]>([]);
  const [schemaPreviews, setSchemaPreviews] = useState<
    Record<string, { document: DocumentRecord; extractionMap: Record<string, ExtractionRecord> }>
  >({});

  const refresh = async () => {
    const [documents, existingSchemas] = await Promise.all([listDocuments(params.caseId), listSchemas(params.caseId)]);
    const known = new Map(existingSchemas.map((item) => [item.document_category, item]));
    const categories = Array.from(
      new Set(
        documents
          .map((item) => item.user_category || item.auto_category)
          .filter((value): value is string => Boolean(value)),
      ),
    );

    const missing = [];
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
        } satisfies SchemaRecord);
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
      if (!current) {
        latestDocsByCategory.set(category, document);
        continue;
      }
      const currentApproved = current.classification_status === "user_approved";
      const nextApproved = document.classification_status === "user_approved";
      if ((nextApproved && !currentApproved) || new Date(document.updated_at) > new Date(current.updated_at)) {
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
  };

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Configuration
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">
            Extraction Schemas
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-dim">
            Tune required fields and output structure category by category. Use the quick jump to move between schemas
            and the in-card filters to narrow large field lists.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="neutral">{schemas.length} schemas</Badge>
          <Badge tone="info">
            {schemas.reduce((count, schema) => count + (schema.fields as SchemaField[]).filter((field) => field.required).length, 0)} required
            fields
          </Badge>
        </div>
      </div>

      {schemas.length > 0 && (
        <div className="rounded-2xl border border-white/[0.06] bg-surface-200/30 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Quick Jump</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {schemas.map((schema) => (
              <a
                key={`jump-${schema.document_category}-${schema.id}`}
                href={`#schema-${schema.document_category}`}
                className="inline-flex rounded-xl border border-white/[0.08] bg-surface-100/60 px-3 py-2 text-sm text-slate transition-all duration-200 hover:border-white/[0.14] hover:bg-surface-100 hover:text-slate-bright"
              >
                {schema.document_category}
              </a>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-6">
        {schemas.map((schema) => (
          <SchemaEditor
            key={`${schema.document_category}-${schema.id}`}
            category={schema.document_category}
            initialFields={schema.fields as SchemaField[]}
            extractionPreview={schemaPreviews[schema.document_category]?.extractionMap}
            previewDocumentName={schemaPreviews[schema.document_category]?.document.original_filename ?? null}
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
        ))}

        {schemas.length === 0 && (
          <div className="panel p-10 text-center">
            <p className="text-sm text-slate-dim">
              Upload documents to generate extraction schemas.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
