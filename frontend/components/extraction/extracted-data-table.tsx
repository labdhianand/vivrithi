"use client";

import { useEffect, useState } from "react";

import type { ExtractionRecord, SelectedExtractionField } from "@/lib/types";
import { cn } from "@/lib/utils";
import { getExtractionFieldLabel, hasExtractionBBox, toSelectedExtractionField } from "@/lib/extraction-highlight";
import { ConfidenceBadge } from "@/components/extraction/confidence-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function ExtractedDataTable({
  extractions,
  selectedExtractionId,
  onSelectField,
  onSave,
}: {
  extractions: ExtractionRecord[];
  selectedExtractionId?: string;
  onSelectField?: (field: SelectedExtractionField) => void;
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

  const handleSelect = (entry: ExtractionRecord) => {
    const selection = toSelectedExtractionField(entry);
    if (selection) {
      onSelectField?.(selection);
    }
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
          const isActive = selectedExtractionId === entry.id;
          const isEdited = entry.user_verified;
          const isMissingRequired = entry.extraction_method === "missing_required";
          const isMissing = !entry.user_edited_value && !entry.value;

          return (
            <div
              key={entry.id}
              className={cn(
                "cursor-pointer border-l-2 p-4 transition-all duration-200",
                isActive
                  ? "border-[#e91e8c] bg-[#3d1a2a]"
                  : index % 2 === 0
                    ? "border-transparent bg-[#2d1420]/60"
                    : "border-transparent bg-transparent",
                !isActive && "hover:bg-[#2d1420]",
              )}
              onClick={() => handleSelect(entry)}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-bright">
                      {getExtractionFieldLabel(entry)}
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
                    {hasExtractionBBox(entry) && (
                      <Badge tone="neutral">Boxed</Badge>
                    )}
                  </div>
                </div>
                <ConfidenceBadge confidence={entry.confidence} />
              </div>

              {isMissingRequired ? (
                <div className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/[0.08] px-3 py-2 text-sm text-rose-100">
                  This compulsory field could not be extracted reliably from the source document and needs manual review.
                </div>
              ) : null}

              <div className="mt-3 flex items-end gap-3">
                <div className="flex-1">
                  <Input
                    value={drafts[entry.id] || ""}
                    placeholder={isMissing ? "No extracted value" : undefined}
                    onClick={(event) => event.stopPropagation()}
                    onChange={(event) => setDrafts((current) => ({ ...current, [entry.id]: event.target.value }))}
                  />
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!entry.source_page_number}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleSelect(entry);
                  }}
                >
                  Locate
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={saving === entry.id}
                  onClick={(event) => {
                    event.stopPropagation();
                    void handleSave(entry.id);
                  }}
                >
                  {saving === entry.id ? "Saving..." : "Save"}
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {extractions.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-slate-dim">No extractions available.</p>
        </div>
      ) : null}
    </Card>
  );
}
