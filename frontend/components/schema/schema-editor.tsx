"use client";

import { useEffect, useState } from "react";

import type { SchemaField } from "@/lib/types";
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
  onSave,
}: {
  category: string;
  initialFields: SchemaField[];
  onSave: (fields: SchemaField[]) => Promise<void>;
}) {
  const [fields, setFields] = useState<SchemaField[]>(initialFields);
  const [busy, setBusy] = useState(false);

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

  return (
    <Card className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Schema
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">{category}</h3>
        </div>
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

      {/* Column headers */}
      <div className="hidden px-4 md:grid md:grid-cols-[1.1fr_1.2fr_0.9fr_100px_80px] md:gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Key</p>
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Label</p>
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Type</p>
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Required</p>
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Action</p>
      </div>

      {/* Field rows */}
      <div className="space-y-2">
        {fields.map((field, index) => (
          <div
            key={`${field.key}-${index}`}
            className={cn(
              "grid gap-3 rounded-xl border border-white/[0.06] p-4",
              "md:grid-cols-[1.1fr_1.2fr_0.9fr_100px_80px]",
              index % 2 === 0 ? "bg-surface-200/40" : "bg-surface-100/30",
              "transition-all duration-200 hover:border-white/[0.12] hover:bg-surface-200/60",
            )}
          >
            <Input
              value={field.key}
              placeholder="field_key"
              onChange={(event) => updateField(index, { key: event.target.value })}
            />
            <Input
              value={field.label}
              placeholder="Label"
              onChange={(event) => updateField(index, { label: event.target.value })}
            />
            <Select value={field.type} onChange={(event) => updateField(index, { type: event.target.value })}>
              {FIELD_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>

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
              <span className="text-xs">Req</span>
            </label>

            <Button
              variant="danger"
              size="sm"
              onClick={() => setFields((current) => current.filter((_, i) => i !== index))}
            >
              Remove
            </Button>
          </div>
        ))}
      </div>

      {fields.length === 0 && (
        <div className="rounded-xl border border-dashed border-white/[0.06] py-8 text-center">
          <p className="text-sm text-slate-dim">No fields defined. Click "Add field" to begin.</p>
        </div>
      )}

      {/* Footer actions */}
      <div className="flex items-center justify-between border-t border-white/[0.06] pt-4">
        <Badge tone="neutral">{fields.length} fields</Badge>
        <Button variant="primary" disabled={busy} onClick={handleSave}>
          {busy ? "Saving\u2026" : "Save schema"}
        </Button>
      </div>
    </Card>
  );
}
