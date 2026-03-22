"use client";

import { useEffect, useMemo, useState } from "react";

import { discoverExtractionFields } from "@/lib/api";
import type { DiscoveredSchemaField, SchemaField } from "@/lib/types";

const FIELD_TYPE_LABELS: Record<string, string> = {
  text: "Text",
  number: "Number",
  percentage: "Percentage",
  currency_crore: "Currency (Cr)",
  currency_lakhs: "Currency (Lakhs)",
  date: "Date",
};

function cloneFields(fields: SchemaField[]) {
  return fields.map((field) => ({ ...field }));
}

function normalizeFieldName(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function toSchemaFieldType(fieldType: string) {
  const normalized = fieldType.trim().toLowerCase();
  if (normalized === "number") {
    return "number";
  }
  if (normalized === "percentage") {
    return "percentage";
  }
  if (normalized === "date") {
    return "date";
  }
  return "text";
}

function createFieldKey(label: string, existingKeys: Set<string>) {
  const baseKey = label.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "dynamic_field";
  let nextKey = baseKey;
  let suffix = 2;
  while (existingKeys.has(nextKey)) {
    nextKey = `${baseKey}_${suffix}`;
    suffix += 1;
  }
  return nextKey;
}

function LockIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 text-[#f48fb1]" fill="none" viewBox="0 0 24 24">
      <path
        d="M7 10V8a5 5 0 0 1 10 0v2m-9 0h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

export function SchemaEditor({
  category,
  initialFields,
  standardFields,
  previewDocumentName,
  previewDocumentId,
  extractionStatus,
  schemaId,
  onSave,
  onRunExtraction,
}: {
  category: string;
  initialFields: SchemaField[];
  standardFields: SchemaField[];
  previewDocumentName?: string | null;
  previewDocumentId?: string | null;
  extractionStatus?: string | null;
  schemaId?: string;
  onSave: (fields: SchemaField[]) => Promise<void>;
  onRunExtraction?: () => Promise<void>;
}) {
  const [removedStandardKeys, setRemovedStandardKeys] = useState<string[]>([]);
  const [addedDynamicFields, setAddedDynamicFields] = useState<SchemaField[]>([]);
  const [discoveredFields, setDiscoveredFields] = useState<DiscoveredSchemaField[]>([]);
  const [ignoredFieldNames, setIgnoredFieldNames] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanAttempted, setScanAttempted] = useState(false);
  const [autoScannedDocId, setAutoScannedDocId] = useState<string | null>(null);

  const rootId = schemaId ? `schema-${schemaId}` : `schema-${category}`;
  const initialSignature = JSON.stringify(initialFields);
  const standardSignature = JSON.stringify(standardFields);

  useEffect(() => {
    const standardKeySet = new Set(standardFields.map((field) => field.key));
    setRemovedStandardKeys(standardFields.filter((field) => !initialFields.some((item) => item.key === field.key)).map((field) => field.key));
    setAddedDynamicFields(cloneFields(initialFields.filter((field) => !standardKeySet.has(field.key))));
    setDiscoveredFields([]);
    setIgnoredFieldNames([]);
    setSaveNotice(null);
    setScanError(null);
    setScanAttempted(false);
    setAutoScannedDocId(null);
  }, [category, initialSignature, standardSignature]);

  const removedKeySet = useMemo(() => new Set(removedStandardKeys), [removedStandardKeys]);
  const addedDynamicNameSet = useMemo(
    () => new Set(addedDynamicFields.map((field) => normalizeFieldName(field.label))),
    [addedDynamicFields],
  );
  const ignoredNameSet = useMemo(() => new Set(ignoredFieldNames), [ignoredFieldNames]);

  const activeStandardFields = standardFields.filter((field) => !removedKeySet.has(field.key));
  const combinedFields = [...activeStandardFields, ...addedDynamicFields];
  const canScan = Boolean(
    previewDocumentId
      && (extractionStatus === "extracted" || extractionStatus === "extraction_failed"),
  );

  const visibleDiscoveredFields = discoveredFields.filter((field) => {
    const normalized = normalizeFieldName(field.field_name);
    return !ignoredNameSet.has(normalized) && !addedDynamicNameSet.has(normalized);
  });

  const scanForAdditionalFields = async ({ isAuto = false }: { isAuto?: boolean } = {}) => {
    if (!previewDocumentId) {
      return;
    }
    try {
      setScanning(true);
      setScanError(null);
      if (!isAuto) {
        setIgnoredFieldNames([]);
      }
      const existingNames = new Set([
        ...standardFields.map((field) => normalizeFieldName(field.label)),
        ...addedDynamicFields.map((field) => normalizeFieldName(field.label)),
      ]);
      const response = await discoverExtractionFields(previewDocumentId);
      setDiscoveredFields(
        response.filter((field) => !existingNames.has(normalizeFieldName(field.field_name))),
      );
      setScanAttempted(true);
    } catch (error) {
      setScanError(error instanceof Error ? error.message : "Unable to scan this document right now.");
      setScanAttempted(true);
    } finally {
      setScanning(false);
      if (previewDocumentId) {
        setAutoScannedDocId(previewDocumentId);
      }
    }
  };

  useEffect(() => {
    if (!previewDocumentId || !canScan || autoScannedDocId === previewDocumentId) {
      return;
    }
    void scanForAdditionalFields({ isAuto: true });
  }, [autoScannedDocId, canScan, previewDocumentId]);

  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6 shadow-sm" id={rootId}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-xl font-semibold text-[#fce4ec]">{category.replace(/_/g, " ")}</h3>
          <p className="mt-1 text-sm text-[#ad6883]">{combinedFields.length} fields included in the final schema.</p>
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
                await onSave(combinedFields);
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

      <div className="mt-6 rounded-xl border border-[#4a1530] bg-[#2d1420] p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <LockIcon />
              <h4 className="text-lg font-semibold text-[#fce4ec]">Standard Fields</h4>
            </div>
            <p className="mt-1 text-sm text-[#ad6883]">
              Pre-configured fields for this document type. Remove fields you don&apos;t need.
            </p>
          </div>
          <span className="rounded-full border border-[#7a2550] px-3 py-1 text-xs font-medium text-[#f48fb1]">
            Locked set
          </span>
        </div>

        <div className="mt-4 space-y-3">
          {standardFields.map((field) => {
            const removed = removedKeySet.has(field.key);
            return (
              <div
                key={field.key}
                className={`grid gap-3 rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 md:grid-cols-[1fr_180px_120px] ${
                  removed ? "opacity-70" : ""
                }`}
              >
                <div>
                  <p className={`text-sm font-medium text-[#fce4ec] ${removed ? "line-through text-[#ad6883]" : ""}`}>
                    {field.label}
                  </p>
                  <p className="mt-1 text-xs text-[#ad6883]">{field.key}</p>
                </div>
                <div className="flex items-center rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-sm text-[#f48fb1]">
                  {FIELD_TYPE_LABELS[field.type] || field.type}
                </div>
                {removed ? (
                  <button
                    type="button"
                    onClick={() => {
                      setRemovedStandardKeys((current) => current.filter((key) => key !== field.key));
                      setSaveNotice(null);
                    }}
                    className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
                  >
                    Restore
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setRemovedStandardKeys((current) => [...current, field.key]);
                      setSaveNotice(null);
                    }}
                    className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
                  >
                    X
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => {
              setRemovedStandardKeys([]);
              setSaveNotice(null);
            }}
            className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-4 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
          >
            Reset to defaults
          </button>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-[#4a1530] bg-[#2d1420] p-5">
        {addedDynamicFields.length > 0 ? (
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-[#fce4ec]">Added Dynamic Fields</h4>
            <p className="mt-1 text-sm text-[#ad6883]">Fields you added from AI discovery are included in the saved schema.</p>
            <div className="mt-4 space-y-3">
              {addedDynamicFields.map((field) => (
                <div
                  key={field.key}
                  className="grid gap-3 rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 md:grid-cols-[1fr_180px_120px]"
                >
                  <div>
                    <p className="text-sm font-medium text-[#fce4ec]">{field.label}</p>
                    <p className="mt-1 text-xs text-[#ad6883]">{field.key}</p>
                  </div>
                  <div className="flex items-center rounded-lg border border-[#4a1530] bg-[#2d1420] px-3 py-2 text-sm text-[#f48fb1]">
                    {FIELD_TYPE_LABELS[field.type] || field.type}
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setAddedDynamicFields((current) => current.filter((item) => item.key !== field.key));
                      setSaveNotice(null);
                    }}
                    className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h4 className="text-lg font-semibold text-[#fce4ec]">AI-Discovered Fields</h4>
            <p className="mt-1 text-sm text-[#ad6883]">Additional fields found by AI in this document</p>
          </div>
          <button
            type="button"
            disabled={!previewDocumentId || scanning || !canScan}
            onClick={() => void scanForAdditionalFields()}
            className="rounded-lg bg-[#1c8f52] px-4 py-2 text-sm font-medium text-[#fce4ec] transition-colors hover:bg-[#157445] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {scanning ? "Scanning document for additional fields..." : "Scan for additional fields"}
          </button>
        </div>

        {!previewDocumentId ? (
          <div className="mt-4 rounded-xl border border-dashed border-[#7a2550] px-4 py-4 text-sm text-[#ad6883]">
            Upload a document for this category to enable discovery.
          </div>
        ) : null}

        {previewDocumentId && !canScan ? (
          <div className="mt-4 rounded-xl border border-dashed border-[#7a2550] px-4 py-4 text-sm text-[#ad6883]">
            Discovery starts after extraction completes for this document.
          </div>
        ) : null}

        {scanError ? (
          <div className="mt-4 rounded-xl border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300">
            {scanError}
          </div>
        ) : null}

        {scanning ? (
          <div className="mt-4 rounded-xl border border-[#4a1530] bg-[#1f0d16] px-4 py-3 text-sm text-[#f48fb1]">
            Scanning document for additional fields...
          </div>
        ) : null}

        <div className="mt-4 space-y-3">
          {visibleDiscoveredFields.map((field) => (
            <div
              key={field.field_name}
              className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium text-[#fce4ec]">{field.field_name}</p>
                    <span className="rounded-full border border-[#7a2550] px-2 py-1 text-xs text-[#f48fb1]">
                      {field.field_type}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-[#f48fb1]">{field.value_found}</p>
                  <p className="mt-2 text-xs text-[#ad6883]">{field.reason}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const existingKeys = new Set([...standardFields, ...addedDynamicFields].map((item) => item.key));
                      setAddedDynamicFields((current) => [
                        ...current,
                        {
                          key: createFieldKey(field.field_name, existingKeys),
                          label: field.field_name,
                          type: toSchemaFieldType(field.field_type),
                          required: false,
                          description: field.reason,
                        },
                      ]);
                      setSaveNotice(null);
                    }}
                    className="rounded-lg bg-[#1c8f52] px-3 py-2 text-sm font-medium text-[#fce4ec] transition-colors hover:bg-[#157445]"
                  >
                    Add to schema
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIgnoredFieldNames((current) => [...current, normalizeFieldName(field.field_name)]);
                    }}
                    className="rounded-lg border border-[#5a5962] bg-[#2a2930] px-3 py-2 text-sm font-medium text-[#d0c9d0] transition-colors hover:bg-[#37353e]"
                  >
                    Ignore
                  </button>
                </div>
              </div>
            </div>
          ))}

          {!scanning && scanAttempted && visibleDiscoveredFields.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[#7a2550] px-4 py-6 text-center text-sm text-[#ad6883]">
              No additional fields discovered in this document
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
