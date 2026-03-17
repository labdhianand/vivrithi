"use client";

import { useEffect, useState } from "react";

import type { ExtractionRecord } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ConfidenceBadge } from "@/components/extraction/confidence-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function ExtractedDataTable({
  extractions,
  activeExtractionId,
  onHighlight,
  onSave,
}: {
  extractions: ExtractionRecord[];
  activeExtractionId?: string;
  onHighlight?: (id: string) => void;
  onSave: (extractionId: string, value: string) => Promise<void>;
}) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    const next: Record<string, string> = {};
    extractions.forEach((entry) => {
      next[entry.id] = entry.user_edited_value || entry.value || "";
    });
    setDrafts(next);
  }, [extractions]);

  const handleSave = async (extractionId: string) => {
    setSaving(extractionId);
    await onSave(extractionId, drafts[extractionId] || "");
    setSaving(null);
  };

  return (
    <Card className="overflow-hidden border-[#4a1530] bg-[#1f0d16]">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Results</p>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">Structured Extraction</h3>
        </div>
        <Badge tone="neutral">{extractions.length} fields</Badge>
      </div>

      <div className="mb-2 grid grid-cols-[1fr_auto] gap-4 px-4">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Field</p>
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Confidence</p>
      </div>

      <div className="space-y-0 divide-y divide-[#4a1530]">
        {extractions.map((entry, index) => {
          const isActive = activeExtractionId === entry.id;
          const isEdited = entry.user_verified;
          const isMissingRequired = entry.extraction_method === "missing_required";
          const isMissing = !entry.user_edited_value && !entry.value;
          return (
            <div
              key={entry.id}
              className={cn(
                "rounded-lg p-4 transition-all duration-200",
                isActive
                  ? "border border-accent/30 bg-accent/[0.06]"
                  : index % 2 === 0
                    ? "bg-[#2d1420]/60"
                    : "bg-transparent",
                !isActive && "hover:bg-[#2d1420]",
              )}
              onMouseEnter={() => onHighlight?.(entry.id)}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-bright">
                      {entry.field_label || entry.schema_field_key}
                    </span>
                    {isEdited && <Badge tone="success">Verified</Badge>}
                    {isMissingRequired && <Badge tone="danger">Required Missing</Badge>}
                    {isMissing && !isMissingRequired && (
                      <span className="rounded-md bg-amber-950 px-2 py-1 text-[11px] font-medium text-amber-300">
                        Null value
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                    {entry.value_type}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {entry.source_page_number && (
                      <Badge tone="info">Page {entry.source_page_number}</Badge>
                    )}
                    {entry.extraction_method && (
                      <Badge tone="neutral">{entry.extraction_method}</Badge>
                    )}
                    {(entry.bbox_x1 || entry.bbox_y1 || entry.bbox_x2 || entry.bbox_y2) && (
                      <Badge tone="neutral">Boxed</Badge>
                    )}
                  </div>
                </div>
                <ConfidenceBadge confidence={entry.confidence} />
              </div>

              {isMissingRequired && (
                <div className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/[0.08] px-3 py-2 text-sm text-rose-100">
                  This compulsory field could not be extracted reliably from the source document and needs manual review.
                </div>
              )}

              <div className="mt-3 flex items-end gap-3">
                <div className="flex-1">
                  <Input
                    value={drafts[entry.id] || ""}
                    placeholder={isMissing ? "No extracted value" : undefined}
                    onChange={(event) => setDrafts((current) => ({ ...current, [entry.id]: event.target.value }))}
                  />
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!entry.source_page_number}
                  onClick={() => onHighlight?.(entry.id)}
                >
                  Locate
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={saving === entry.id}
                  onClick={() => handleSave(entry.id)}
                >
                  {saving === entry.id ? "Saving\u2026" : "Save"}
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {extractions.length === 0 && (
        <div className="py-8 text-center">
          <p className="text-sm text-slate-dim">No extractions available.</p>
        </div>
      )}
    </Card>
  );
}
