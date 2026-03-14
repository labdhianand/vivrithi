"use client";

import { useEffect, useState } from "react";

import { getDefaultSchema, listDocuments, listSchemas, saveSchema, updateSchema } from "@/lib/api";
import type { SchemaField, SchemaRecord } from "@/lib/types";
import { SchemaEditor } from "@/components/schema/schema-editor";
import { Badge } from "@/components/ui/badge";

export default function SchemaPage({ params }: { params: { caseId: string } }) {
  const [schemas, setSchemas] = useState<SchemaRecord[]>([]);

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
  };

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Configuration
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">
            Extraction Schemas
          </h2>
        </div>
        <Badge tone="neutral">{schemas.length} schemas</Badge>
      </div>

      <div className="space-y-6">
        {schemas.map((schema) => (
          <SchemaEditor
            key={`${schema.document_category}-${schema.id}`}
            category={schema.document_category}
            initialFields={schema.fields as SchemaField[]}
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
