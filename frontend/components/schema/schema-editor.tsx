"use client";

import { useEffect, useState } from "react";

import type { ExtractionRecord, SchemaField } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

const FIELD_TYPES = ["text", "number", "percentage", "currency_lakhs", "currency_crore", "date", "json"];

export function SchemaEditor({
  category,
  initialFields,
  extractionPreview,
  previewDocumentName,
  onSave,
}: {
  category: string;
  initialFields: SchemaField[];
  extractionPreview?: Record<string, ExtractionRecord>;
  previewDocumentName?: string | null;
  onSave: (fields: SchemaField[]) => Promise<void>;
}) {
  const [fields, setFields] = useState<SchemaField[]>(initialFields);
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [requirementFilter, setRequirementFilter] = useState("all");

  useEffect(() => {
    setFields(initialFields);
  }, [initialFields]);

  const updateField = (index: number, partial: Partial<SchemaField>) => {
    setFields((current) =>
      current.map((field, currentIndex) => (currentIndex === index ? { ...field, ...partial } : field)),
    );
  };

  const handleSave = async () => {
    setBusy(true);
    await onSave(fields);
    setBusy(false);
  };

  const visibleFields = fields
    .map((field, index) => ({ field, index }))
    .filter(({ field }) => {
      const query = search.trim().toLowerCase();
      const matchesSearch =
        !query ||
        field.key.toLowerCase().includes(query) ||
        field.label.toLowerCase().includes(query) ||
        (field.description || "").toLowerCase().includes(query);
      const matchesType = typeFilter === "all" || field.type === typeFilter;
      const matchesRequirement =
        requirementFilter === "all" ||
        (requirementFilter === "required" && field.required) ||
        (requirementFilter === "optional" && !field.required);
      return matchesSearch && matchesType && matchesRequirement;
    });

  const requiredCount = fields.filter((field) => field.required).length;
  const optionalCount = fields.length - requiredCount;

  const summarizePreviewValue = (field: SchemaField, preview: ExtractionRecord | undefined) => {
    const rawValue = preview?.user_edited_value || preview?.value || "";
    if (!rawValue) {
      return null;
    }

    if (field.type === "json") {
      try {
        const parsed = JSON.parse(rawValue);
        if (Array.isArray(parsed)) {
          const first = parsed[0];
          if (first && typeof first === "object") {
            const sample = Object.values(first)
              .filter((value) => value !== null && value !== undefined && `${value}`.trim())
              .slice(0, 2)
              .join(" | ");
            return `${parsed.length} item${parsed.length === 1 ? "" : "s"}${sample ? `: ${sample}` : ""}`;
          }
          return `${parsed.length} item${parsed.length === 1 ? "" : "s"}`;
        }
        if (parsed && typeof parsed === "object") {
          return `${Object.keys(parsed).length} keys`;
        }
      } catch {
        // Fall through to text summarization if the payload is not valid JSON.
      }
    }

    const compact = rawValue.replace(/\s+/g, " ").trim();
    if (compact.length <= 140) {
      return compact;
    }
    return `${compact.slice(0, 137)}...`;
  };

  return (
    <Card className="space-y-5" id={`schema-${category}`}>
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Schema
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">{category}</h3>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone="neutral">{fields.length} total fields</Badge>
            <Badge tone="info">{requiredCount} required</Badge>
            <Badge tone="neutral">{optionalCount} optional</Badge>
            {previewDocumentName && <Badge tone="success">Previewing {previewDocumentName}</Badge>}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              setFields((current) => [
                ...current,
                { key: "", label: "", type: "text", required: false, description: "" },
              ])
            }
          >
            + Add field
          </Button>
        </div>
      </div>

      <div className="grid gap-3 rounded-2xl border border-white/[0.06] bg-surface-200/30 p-4 lg:grid-cols-[1.4fr_180px_180px_auto]">
        <Input
          value={search}
          placeholder="Search by key, label, or notes"
          onChange={(event) => setSearch(event.target.value)}
        />
        <Select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
          <option value="all">All types</option>
          {FIELD_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </Select>
        <Select value={requirementFilter} onChange={(event) => setRequirementFilter(event.target.value)}>
          <option value="all">All fields</option>
          <option value="required">Required only</option>
          <option value="optional">Optional only</option>
        </Select>
        <div className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.06] px-4 py-2 text-sm text-slate lg:justify-center">
          <span>Showing</span>
          <Badge tone="neutral">{visibleFields.length}</Badge>
        </div>
      </div>

      {/* Field rows */}
      <div className="space-y-2">
        <div className="hidden px-4 lg:grid lg:grid-cols-[110px_1fr_1fr_0.8fr_1.05fr_140px_90px] lg:gap-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Field</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Key</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Label</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Type</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Extracted Value</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Requirement</p>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Action</p>
        </div>

        {visibleFields.map(({ field, index }) => (
          <div
            key={`${field.key}-${index}`}
            className={cn(
              "grid gap-3 overflow-hidden rounded-2xl border border-white/[0.06] p-4",
              "lg:grid-cols-[110px_1fr_1fr_0.8fr_1.05fr_140px_90px]",
              index % 2 === 0 ? "bg-surface-200/40" : "bg-surface-100/30",
              "transition-all duration-200 hover:border-white/[0.12] hover:bg-surface-200/60",
            )}
          >
            {(() => {
              const preview = extractionPreview?.[field.key];
              const previewValue = preview?.user_edited_value || preview?.value || null;
              const isMissingRequired = !previewValue && field.required;
              const previewSummary = summarizePreviewValue(field, preview);
              return (
                <>
            <div className="min-w-0 flex items-center gap-2">
              <Badge tone={field.required ? "info" : "neutral"}>{field.required ? "Required" : "Optional"}</Badge>
              <span className="text-xs text-slate-dim">#{index + 1}</span>
            </div>

            <div className="min-w-0">
              <Input
                value={field.key}
                placeholder="field_key"
                onChange={(event) => updateField(index, { key: event.target.value })}
              />
            </div>
            <div className="min-w-0">
              <Input
                value={field.label}
                placeholder="Label"
                onChange={(event) => updateField(index, { label: event.target.value })}
              />
            </div>
            <div className="min-w-0">
              <Select value={field.type} onChange={(event) => updateField(index, { type: event.target.value })}>
                {FIELD_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </Select>
            </div>

            <div className="min-w-0 rounded-xl border border-white/[0.06] bg-surface-200/70 px-3 py-2.5">
              <div className="flex items-start justify-between gap-2">
                <p
                  className={cn("min-w-0 text-sm leading-5", previewValue ? "text-slate-bright" : "text-slate-dim")}
                  title={previewValue || undefined}
                >
                  <span className="block overflow-hidden text-ellipsis whitespace-nowrap">
                    {previewSummary || (field.required ? "Missing required value" : "No extracted value")}
                  </span>
                </p>
                {preview?.confidence && (
                  <Badge tone="neutral" className="shrink-0">
                    {Math.round(Number(preview.confidence) * 100)}%
                  </Badge>
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {preview?.source_page_number && <Badge tone="info">Page {preview.source_page_number}</Badge>}
                {preview?.extraction_method && (
                  <Badge tone={isMissingRequired ? "danger" : "neutral"}>{preview.extraction_method}</Badge>
                )}
                {field.type === "json" && previewValue && <Badge tone="neutral">JSON preview</Badge>}
                {isMissingRequired && !preview?.extraction_method && <Badge tone="danger">missing_required</Badge>}
              </div>
            </div>

            {/* Required checkbox - dark themed */}
            <label
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-xl border border-white/[0.06] px-3 py-2.5 text-sm transition-all duration-200",
                "bg-surface-200 text-slate hover:border-white/[0.12]",
                field.required && "border-accent/30 text-accent-glow",
              )}
            >
              <input
                checked={field.required}
                type="checkbox"
                className="accent-accent"
                onChange={(event) => updateField(index, { required: event.target.checked })}
              />
              <span className="text-xs">{field.required ? "Required" : "Optional"}</span>
            </label>

            <Button
              variant="danger"
              size="sm"
              onClick={() => setFields((current) => current.filter((_, i) => i !== index))}
            >
              Remove
            </Button>
                </>
              );
            })()}
          </div>
        ))}
      </div>

      {visibleFields.length === 0 && (
        <div className="rounded-xl border border-dashed border-white/[0.06] py-8 text-center">
          <p className="text-sm text-slate-dim">
            {fields.length === 0
              ? 'No fields defined. Click "+ Add field" to begin.'
              : "No fields match the current search or filters."}
          </p>
        </div>
      )}

      {/* Footer actions */}
      <div className="flex flex-col gap-3 border-t border-white/[0.06] pt-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-dim">
          <Badge tone="neutral">{fields.length} fields</Badge>
          <span>Required fields are treated as compulsory during extraction review.</span>
        </div>
        <Button variant="primary" disabled={busy} onClick={handleSave}>
          {busy ? "Saving\u2026" : "Save schema"}
        </Button>
      </div>
    </Card>
  );
}
