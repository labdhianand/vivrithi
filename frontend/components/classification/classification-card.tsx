"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { DOCUMENT_CATEGORIES } from "@/lib/utils";
import type { DocumentRecord } from "@/lib/types";

function confidenceTone(score: number): "default" | "success" | "warn" | "danger" {
  if (score >= 0.85) return "success";
  if (score >= 0.6) return "warn";
  return "danger";
}

export function ClassificationCard({
  document,
  onApprove,
}: {
  document: DocumentRecord;
  onApprove: (category: string) => Promise<void>;
}) {
  const [category, setCategory] = useState(document.user_category || document.auto_category || "ALM");
  const [approving, setApproving] = useState(false);
  const confidence = document.auto_category_confidence ? Number(document.auto_category_confidence) : 0;
  const confidencePercent = Math.round(confidence * 100);
  const readyForApproval = ["extracted", "completed"].includes(document.processing_status);
  const alreadyApproved = ["approved", "user_approved"].includes(document.classification_status);

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-6">
        {/* Left: Document info */}
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Classifier output
          </p>
          <h3 className="mt-2 truncate text-base font-semibold text-slate-bright">
            {document.original_filename}
          </h3>

          {/* Classification status row */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone={alreadyApproved ? "success" : "neutral"}>
              {document.classification_status}
            </Badge>
            <Badge
              tone={document.processing_status === "extracted" || document.processing_status === "completed" ? "success" : document.processing_status === "failed" ? "danger" : "info"}
              pulse={!readyForApproval && document.processing_status !== "failed"}
            >
              {document.processing_status}
            </Badge>
          </div>

          {/* Auto-detected category with confidence */}
          <div className="mt-4 rounded-xl border border-white/[0.06] bg-surface-200/60 p-3.5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                  Auto-detected category
                </p>
                <p className="mt-1 text-sm font-medium text-slate-bright">
                  {document.auto_category || "Pending"}
                </p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                  Confidence
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <Badge tone={confidenceTone(confidence)}>
                    {confidencePercent}%
                  </Badge>
                </div>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="mt-3">
              <div className="h-1.5 overflow-hidden rounded-full bg-surface">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    confidence >= 0.85
                      ? "bg-gradient-to-r from-emerald to-emerald-glow"
                      : confidence >= 0.6
                        ? "bg-gradient-to-r from-gold to-gold-glow"
                        : "bg-gradient-to-r from-rose to-rose-glow"
                  }`}
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="w-full shrink-0 space-y-4 md:w-[260px]">
          {!readyForApproval ? (
            <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                Processing status
              </p>
              <p className="mt-2 text-sm text-slate-bright">
                {document.processing_status === "failed"
                  ? "Processing failed. Re-upload or retry from the backend."
                  : "This document is still processing. Approval will appear automatically when extraction finishes."}
              </p>
            </div>
          ) : alreadyApproved ? (
            <div className="rounded-xl border border-emerald/20 bg-emerald/10 p-4">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-emerald-glow/70">
                Approved category
              </p>
              <p className="mt-2 text-sm font-medium text-emerald-glow">
                {(document.user_category || document.auto_category || category).replace(/_/g, " ")}
              </p>
            </div>
          ) : (
            <>
              <Select
                label="Assign category"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                {DOCUMENT_CATEGORIES.map((option) => (
                  <option key={option} value={option}>
                    {option.replace(/_/g, " ")}
                  </option>
                ))}
              </Select>
              <Button
                className="w-full"
                disabled={approving}
                onClick={async () => {
                  try {
                    setApproving(true);
                    await onApprove(category);
                  } finally {
                    setApproving(false);
                  }
                }}
              >
                {approving ? "Saving..." : "Approve category"}
              </Button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}
