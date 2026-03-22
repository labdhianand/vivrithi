"use client";

import { useState } from "react";

import type { ExtractionRecord, SchemaField } from "@/lib/types";

const FIELD_TYPES = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "percentage", label: "Percentage" },
  { value: "currency_lakhs", label: "Currency (Lakhs)" },
  { value: "currency_crore", label: "Currency (Cr)" },
  { value: "date", label: "Date" },
] as const;

const DEFAULT_FIELDS_BY_CATEGORY: Record<string, SchemaField[]> = {
  GST_Returns: [
    { key: "gstin", label: "GSTIN", type: "text", required: true },
    { key: "filing_period", label: "Filing Period", type: "text", required: true },
    { key: "gross_turnover_crore", label: "Gross Turnover (Cr)", type: "number", required: true },
    { key: "taxable_turnover_crore", label: "Taxable Turnover (Cr)", type: "number", required: true },
    { key: "total_tax_paid_crore", label: "Total Tax Paid (Cr)", type: "number", required: false },
    { key: "input_tax_credit_crore", label: "Input Tax Credit (Cr)", type: "number", required: false },
  ],
  ITR: [
    { key: "pan", label: "PAN", type: "text", required: true },
    { key: "assessment_year", label: "Assessment Year", type: "text", required: true },
    { key: "gross_total_income_crore", label: "Gross Total Income (Cr)", type: "number", required: true },
    { key: "total_deductions_crore", label: "Total Deductions (Cr)", type: "number", required: false },
    { key: "taxable_income_crore", label: "Taxable Income (Cr)", type: "number", required: true },
    { key: "tax_paid_crore", label: "Tax Paid (Cr)", type: "number", required: false },
  ],
  Bank_Statement: [
    { key: "bank_name", label: "Bank Name", type: "text", required: true },
    { key: "account_holder", label: "Account Holder", type: "text", required: true },
    { key: "period", label: "Period", type: "text", required: true },
    { key: "opening_balance_crore", label: "Opening Balance (Cr)", type: "number", required: false },
    { key: "closing_balance_crore", label: "Closing Balance (Cr)", type: "number", required: true },
    { key: "total_credits_crore", label: "Total Credits (Cr)", type: "number", required: true },
    { key: "total_debits_crore", label: "Total Debits (Cr)", type: "number", required: true },
    { key: "average_monthly_balance_crore", label: "Average Monthly Balance (Cr)", type: "number", required: false },
  ],
};

function cloneFields(fields: SchemaField[]) {
  return fields.map((field) => ({ ...field }));
}

export function SchemaEditor({
  category,
  initialFields,
  extractionPreview,
  previewDocumentName,
  previewDocumentId,
  schemaId,
  onSave,
  onRunExtraction,
  onUpdateExtraction,
}: {
  category: string;
  initialFields: SchemaField[];
  extractionPreview?: Record<string, ExtractionRecord>;
  previewDocumentName?: string | null;
  previewDocumentId?: string | null;
  schemaId?: string;
  onSave: (fields: SchemaField[]) => Promise<void>;
  onRunExtraction?: () => Promise<void>;
  onUpdateExtraction?: (extractionId: string, value: string) => Promise<void>;
}) {
  const [fields, setFields] = useState<SchemaField[]>(() =>
    cloneFields(initialFields.length > 0 ? initialFields : DEFAULT_FIELDS_BY_CATEGORY[category] || []),
  );
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [newFieldLabel, setNewFieldLabel] = useState("");
  const [newFieldType, setNewFieldType] = useState("text");
  const [editingFieldKey, setEditingFieldKey] = useState<string | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const [saveNotice, setSaveNotice] = useState<string | null>(null);

  const rootId = schemaId ? `schema-${schemaId}` : `schema-${category}`;

  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6 shadow-sm" id={rootId}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-xl font-semibold text-[#fce4ec]">{category.replace(/_/g, " ")}</h3>
          <p className="mt-1 text-sm text-[#ad6883]">{fields.length} schema fields configured.</p>
          {previewDocumentName ? <p className="mt-2 text-sm text-[#ad6883]">Previewing {previewDocumentName}</p> : null}
          {saveNotice ? <p className="mt-2 text-sm text-green-300">{saveNotice}</p> : null}
        </div>
        <div className="flex flex-wrap gap-3">
          {previewDocumentId && onRunExtraction ? (
            <button
              type="button"
              disabled={extracting}
              onClick={async () => {
                try {
                  setExtracting(true);
                  await onRunExtraction();
                } finally {
                  setExtracting(false);
                }
              }}
              className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-4 py-2 font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530] disabled:opacity-50"
            >
              {extracting ? "Running..." : "Run extraction"}
            </button>
          ) : null}
          <button
            type="button"
            disabled={saving}
            onClick={async () => {
              try {
                setSaving(true);
                setSaveNotice(null);
                await onSave(fields);
                setSaveNotice("Schema saved successfully.");
              } finally {
                setSaving(false);
              }
            }}
            className="rounded-lg bg-[#e91e8c] px-4 py-2 font-medium text-[#fce4ec] transition-colors hover:bg-[#c4187a] disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save schema"}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-3 rounded-xl border border-[#4a1530] bg-[#2d1420] p-4 md:grid-cols-[1fr_220px_120px]">
        <input
          value={newFieldLabel}
          onChange={(event) => setNewFieldLabel(event.target.value)}
          placeholder="Add field label"
          className="w-full rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-[#fce4ec] placeholder:text-[#ad6883] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]"
        />
        <select
          value={newFieldType}
          onChange={(event) => setNewFieldType(event.target.value)}
          className="w-full rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-[#fce4ec] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]"
        >
          {FIELD_TYPES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => {
            if (!newFieldLabel.trim()) {
              return;
            }
            const key = newFieldLabel.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_");
            setFields((current) => [
              ...current,
              { key, label: newFieldLabel.trim(), type: newFieldType, required: false },
            ]);
            setNewFieldLabel("");
            setNewFieldType("text");
            setSaveNotice(null);
          }}
          className="rounded-lg bg-[#e91e8c] px-4 py-2 font-medium text-[#fce4ec] transition-colors hover:bg-[#c4187a]"
        >
          Add
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {fields.map((field) => (
          <div key={field.key} className="grid gap-3 rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 md:grid-cols-[1.3fr_180px_120px_80px]">
            <div>
              <p className="text-sm font-medium text-[#fce4ec]">{field.label}</p>
              <p className="mt-1 text-xs text-[#ad6883]">{field.key}</p>
            </div>
            <select
              value={field.type}
              onChange={(event) =>
                setFields((current) =>
                  current.map((item) =>
                    item.key === field.key ? { ...item, type: event.target.value } : item,
                  ),
                )
              }
              className="w-full rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-[#fce4ec] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]"
            >
              {FIELD_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-sm text-[#f48fb1]">
              <input
                type="checkbox"
                checked={field.required}
                onChange={(event) =>
                  setFields((current) =>
                    current.map((item) =>
                      item.key === field.key ? { ...item, required: event.target.checked } : item,
                    ),
                  )
                }
              />
              Required
            </label>
            <button
              type="button"
              onClick={() => {
                setFields((current) => current.filter((item) => item.key !== field.key));
                setSaveNotice(null);
              }}
              className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
            >
              X
            </button>
          </div>
        ))}
      </div>

      {fields.length === 0 ? (
        <div className="mt-6 rounded-xl border border-dashed border-[#7a2550] px-4 py-8 text-center text-[#ad6883]">
          No schema fields configured yet.
        </div>
      ) : null}

      <div className="mt-8">
        <h4 className="text-lg font-semibold text-[#fce4ec]">Extraction Results</h4>
        <div className="mt-4 overflow-hidden rounded-xl border border-[#4a1530]">
          <div className="grid grid-cols-[1.2fr_1.4fr_140px] bg-[#2d1420] px-4 py-3 text-sm font-medium text-[#f48fb1]">
            <span>Field</span>
            <span>Extracted Value</span>
            <span>Edit</span>
          </div>
          {fields.map((field) => {
            const preview = extractionPreview?.[field.key];
            const value = preview?.user_edited_value || preview?.value || "";
            const missing = !value;
            const editing = editingFieldKey === field.key;
            return (
              <div key={`preview-${field.key}`} className="grid grid-cols-[1.2fr_1.4fr_140px] border-t border-[#4a1530] bg-[#1f0d16] px-4 py-3 text-sm">
                <span className="font-medium text-[#fce4ec]">{field.label}</span>
                {editing ? (
                  <input
                    value={draftValue}
                    onChange={(event) => setDraftValue(event.target.value)}
                    className="rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-[#fce4ec] placeholder:text-[#ad6883] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]"
                  />
                ) : (
                  <span className={missing ? "rounded-lg bg-amber-950 px-3 py-2 italic text-amber-300" : "text-[#f48fb1]"}>
                    {missing ? "Not found - enter manually" : value}
                  </span>
                )}
                <div>
                  {editing ? (
                    <button
                      type="button"
                      disabled={!preview?.id || !onUpdateExtraction}
                      onClick={async () => {
                        if (!preview?.id || !onUpdateExtraction) {
                          return;
                        }
                        await onUpdateExtraction(preview.id, draftValue);
                        setEditingFieldKey(null);
                      }}
                      className="rounded-lg bg-[#e91e8c] px-3 py-2 text-sm font-medium text-[#fce4ec] transition-colors hover:bg-[#c4187a] disabled:opacity-50"
                    >
                      Save
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingFieldKey(field.key);
                        setDraftValue(value);
                      }}
                      className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
                    >
                      Edit
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
