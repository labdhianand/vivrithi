"use client";

import { useEffect, useMemo, useState } from "react";

import type { ExtractionRecord, SchemaField } from "@/lib/types";

const FIELD_TYPES = [
  { value: "text", label: "Text" },
  { value: "number", label: "Number" },
  { value: "percentage", label: "Percentage" },
  { value: "currency_crore", label: "Currency (Cr)" },
  { value: "date", label: "Date" },
] as const;

const REQUIRED_DEFAULTS: Record<string, SchemaField[]> = {
  Annual_Report: [
    { key: "total_revenue_crore", label: "Revenue FY24 (Cr)", type: "currency_crore", required: true },
    { key: "revenue_fy23_crore", label: "Revenue FY23 (Cr)", type: "currency_crore", required: false },
    { key: "net_profit_fy24_crore", label: "Net Profit FY24 (Cr)", type: "currency_crore", required: false },
    { key: "ebitda_fy24_crore", label: "EBITDA FY24 (Cr)", type: "currency_crore", required: false },
    { key: "total_debt_crore", label: "Total Debt (Cr)", type: "currency_crore", required: false },
    { key: "net_worth_crore", label: "Net Worth (Cr)", type: "currency_crore", required: true },
    { key: "debt_equity_ratio", label: "Debt/Equity Ratio", type: "number", required: false },
    { key: "interest_coverage_ratio", label: "Interest Coverage Ratio", type: "number", required: false },
    { key: "auditor_name", label: "Auditor Name", type: "text", required: false },
    { key: "auditor_opinion", label: "Auditor Opinion", type: "text", required: false },
    { key: "going_concern_flag", label: "Going Concern Flag", type: "text", required: false },
  ],
  ALM: [
    { key: "total_assets_crore", label: "Total Assets (Cr)", type: "currency_crore", required: false },
    { key: "total_liabilities_crore", label: "Total Liabilities (Cr)", type: "currency_crore", required: false },
    { key: "asset_bucket_0_1yr_crore", label: "0-1yr Asset Bucket (Cr)", type: "currency_crore", required: false },
    { key: "liability_bucket_0_1yr_crore", label: "0-1yr Liability Bucket (Cr)", type: "currency_crore", required: false },
    { key: "gap_1_3yr_crore", label: "1-3yr Gap (Cr)", type: "currency_crore", required: false },
    { key: "gap_3_5yr_crore", label: "3-5yr Gap (Cr)", type: "currency_crore", required: false },
    { key: "lcr_ratio", label: "Liquidity Coverage Ratio", type: "percentage", required: true },
    { key: "nsfr_ratio", label: "Net Stable Funding Ratio", type: "percentage", required: false },
  ],
  Shareholding_Pattern: [
    { key: "promoter_holding_percent", label: "Promoter Holding %", type: "percentage", required: true },
    { key: "shares_pledged_percent", label: "Promoter Pledge %", type: "percentage", required: false },
    { key: "fii_holding_percent", label: "FII Holding %", type: "percentage", required: false },
    { key: "dii_holding_percent", label: "DII Holding %", type: "percentage", required: false },
    { key: "public_holding_percent", label: "Public Holding %", type: "percentage", required: false },
    { key: "promoter_holding_change_qoq", label: "Change in Promoter Holding QoQ", type: "percentage", required: false },
  ],
  Borrowing_Profile: [
    { key: "total_outstanding_debt_crore", label: "Total Outstanding Debt (Cr)", type: "currency_crore", required: false },
    { key: "secured_debt_crore", label: "Secured Debt (Cr)", type: "currency_crore", required: false },
    { key: "unsecured_debt_crore", label: "Unsecured Debt (Cr)", type: "currency_crore", required: false },
    { key: "number_of_lenders", label: "Number of Lenders", type: "number", required: false },
    { key: "highest_single_lender_exposure_percent", label: "Highest Single Lender Exposure %", type: "percentage", required: false },
    { key: "average_cost_of_borrowing_percent", label: "Average Cost of Borrowing %", type: "percentage", required: false },
    { key: "nearest_repayment_amount_crore", label: "Nearest Repayment Amount (Cr)", type: "currency_crore", required: false },
    { key: "nearest_repayment_date", label: "Nearest Repayment Date", type: "date", required: false },
  ],
  Portfolio_Performance: [
    { key: "total_aum_crore", label: "Total AUM (Cr)", type: "currency_crore", required: false },
    { key: "gnpa_percent", label: "Gross NPA %", type: "percentage", required: false },
    { key: "nnpa_percent", label: "Net NPA %", type: "percentage", required: false },
    { key: "collection_efficiency_percent", label: "Collection Efficiency %", type: "percentage", required: false },
    { key: "capital_adequacy_ratio", label: "Capital Adequacy Ratio", type: "percentage", required: false },
    { key: "cost_of_funds_percent", label: "Cost of Funds %", type: "percentage", required: false },
    { key: "yield_on_advances_percent", label: "Yield on Advances %", type: "percentage", required: false },
    { key: "aum_growth_yoy_percent", label: "AUM Growth YoY %", type: "percentage", required: false },
  ],
};

function mergeDefaults(category: string, fields: SchemaField[]) {
  const defaults = REQUIRED_DEFAULTS[category] || [];
  const existing = new Map(fields.map((field) => [field.key, field]));
  for (const field of defaults) {
    if (!existing.has(field.key)) {
      existing.set(field.key, field);
    }
  }
  return Array.from(existing.values());
}

export function SchemaEditor({
  category,
  initialFields,
  extractionPreview,
  previewDocumentName,
  previewDocumentId,
  onSave,
  onRunExtraction,
  onUpdateExtraction,
}: {
  category: string;
  initialFields: SchemaField[];
  extractionPreview?: Record<string, ExtractionRecord>;
  previewDocumentName?: string | null;
  previewDocumentId?: string | null;
  onSave: (fields: SchemaField[]) => Promise<void>;
  onRunExtraction?: () => Promise<void>;
  onUpdateExtraction?: (extractionId: string, value: string) => Promise<void>;
}) {
  const [fields, setFields] = useState<SchemaField[]>(() => mergeDefaults(category, initialFields));
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [newFieldLabel, setNewFieldLabel] = useState("");
  const [newFieldType, setNewFieldType] = useState("text");
  const [editingFieldKey, setEditingFieldKey] = useState<string | null>(null);
  const [draftValue, setDraftValue] = useState("");

  useEffect(() => {
    setFields(mergeDefaults(category, initialFields));
  }, [category, initialFields]);

  const orderedFields = useMemo(() => fields, [fields]);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm" id={`schema-${category}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">{category.replace(/_/g, " ")}</h3>
          <p className="mt-1 text-sm text-slate-500">{orderedFields.length} schema fields configured.</p>
          {previewDocumentName ? <p className="mt-2 text-sm text-slate-500">Previewing {previewDocumentName}</p> : null}
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
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
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
                await onSave(fields);
              } finally {
                setSaving(false);
              }
            }}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save schema"}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-[1fr_220px_120px]">
        <input
          value={newFieldLabel}
          onChange={(event) => setNewFieldLabel(event.target.value)}
          placeholder="Add field label"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={newFieldType}
          onChange={(event) => setNewFieldType(event.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            setFields((current) => [...current, { key, label: newFieldLabel.trim(), type: newFieldType, required: false }]);
            setNewFieldLabel("");
            setNewFieldType("text");
          }}
          className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
        >
          Add
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {orderedFields.map((field) => (
          <div key={field.key} className="grid gap-3 rounded-xl border border-slate-200 p-4 md:grid-cols-[1.3fr_180px_120px_80px]">
            <div>
              <p className="text-sm font-medium text-slate-900">{field.label}</p>
              <p className="mt-1 text-xs text-slate-500">{field.key}</p>
            </div>
            <select
              value={field.type}
              onChange={(event) =>
                setFields((current) =>
                  current.map((item) => (item.key === field.key ? { ...item, type: event.target.value } : item)),
                )
              }
              className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {FIELD_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={field.required}
                onChange={(event) =>
                  setFields((current) =>
                    current.map((item) => (item.key === field.key ? { ...item, required: event.target.checked } : item)),
                  )
                }
              />
              Required
            </label>
            <button
              type="button"
              onClick={() => setFields((current) => current.filter((item) => item.key !== field.key))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              X
            </button>
          </div>
        ))}
      </div>

      {orderedFields.length === 0 ? (
        <div className="mt-6 rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-slate-500">
          No schema fields configured yet.
        </div>
      ) : null}

      <div className="mt-8">
        <h4 className="text-lg font-semibold text-slate-900">Extraction Results</h4>
        <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
          <div className="grid grid-cols-[1.2fr_1.4fr_140px] bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700">
            <span>Field</span>
            <span>Extracted Value</span>
            <span>Edit</span>
          </div>
          {orderedFields.map((field) => {
            const preview = extractionPreview?.[field.key];
            const value = preview?.user_edited_value || preview?.value || "";
            const missing = !value;
            const editing = editingFieldKey === field.key;
            return (
              <div key={`preview-${field.key}`} className="grid grid-cols-[1.2fr_1.4fr_140px] border-t border-slate-200 px-4 py-3 text-sm">
                <span className="font-medium text-slate-900">{field.label}</span>
                {editing ? (
                  <input
                    value={draftValue}
                    onChange={(event) => setDraftValue(event.target.value)}
                    className="rounded-lg border border-slate-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <span className={missing ? "rounded-lg bg-amber-50 px-3 py-2 italic text-amber-800" : "text-slate-700"}>
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
                      className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
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
                      className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
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
