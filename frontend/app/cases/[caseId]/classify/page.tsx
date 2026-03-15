"use client";

import { useEffect, useState } from "react";

import { approveClassification, listDocuments, processCaseDocuments, rejectClassification } from "@/lib/api";
import type { DocumentRecord } from "@/lib/types";
import { DOCUMENT_CATEGORIES } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ClassificationCard } from "@/components/classification/classification-card";

const TERMINAL_STATUSES = new Set(["extracted", "completed", "failed"]);
const ACTIVE_STATUSES = new Set(["queued", "triaging", "parsing", "classifying", "extracting", "processing"]);

export default function ClassificationPage({ params }: { params: { caseId: string } }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => listDocuments(params.caseId).then(setDocuments).catch((err) => setError(err.message));
  const startProcessing = async () => {
    setProcessing(true);
    setError(null);
    await processCaseDocuments(params.caseId);
    await refresh();
  };

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  const classifiedCount = documents.filter((d) => d.auto_category || d.user_category).length;
  const finishedCount = documents.filter((d) => TERMINAL_STATUSES.has(d.processing_status)).length;
  const overallProgress = documents.length
    ? Math.round(documents.reduce((sum, document) => sum + (document.progress_percent || 0), 0) / documents.length)
    : 0;

  useEffect(() => {
    if (!processing) {
      return;
    }
    const intervalId = window.setInterval(() => {
      refresh();
    }, 3000);
    return () => window.clearInterval(intervalId);
  }, [processing, params.caseId]);

  useEffect(() => {
    if (processing && documents.length > 0 && documents.every((d) => TERMINAL_STATUSES.has(d.processing_status))) {
      setProcessing(false);
    }
  }, [documents, processing]);

  useEffect(() => {
    if (documents.length === 0) {
      return;
    }
    const hasPending = documents.some((d) => d.processing_status === "pending");
    const hasActive = documents.some((d) => ACTIVE_STATUSES.has(d.processing_status));
    if (hasActive && !processing) {
      setProcessing(true);
      return;
    }
    if (hasPending && !processing) {
      startProcessing().catch((err) => {
        setError(err instanceof Error ? err.message : "Processing failed");
        setProcessing(false);
      });
    }
  }, [documents, processing, params.caseId]);

  // Pack validation: check which of the 5 required categories are covered by approved docs
  const approvedCategories = new Set(
    documents
      .filter((d) => ["approved", "user_approved"].includes(d.classification_status))
      .map((d) => d.user_category || d.auto_category)
      .filter(Boolean),
  );
  const missingCategories = DOCUMENT_CATEGORIES.filter((cat) => !approvedCategories.has(cat));
  const packComplete = missingCategories.length === 0 && documents.length > 0;

  const sortedDocuments = [...documents].sort((left, right) => {
    // Rejected docs go to bottom
    const leftRejected = left.classification_status === "rejected";
    const rightRejected = right.classification_status === "rejected";
    if (leftRejected !== rightRejected) return leftRejected ? 1 : -1;

    const leftReady = ["extracted", "completed"].includes(left.processing_status) && !["approved", "user_approved", "rejected"].includes(left.classification_status);
    const rightReady = ["extracted", "completed"].includes(right.processing_status) && !["approved", "user_approved", "rejected"].includes(right.classification_status);
    if (leftReady !== rightReady) {
      return leftReady ? -1 : 1;
    }
    const leftActive = !TERMINAL_STATUSES.has(left.processing_status);
    const rightActive = !TERMINAL_STATUSES.has(right.processing_status);
    if (leftActive !== rightActive) {
      return leftActive ? 1 : -1;
    }
    return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="animate-fade-in flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Classification
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">
            Document Classification
          </h2>
          <p className="mt-1.5 text-sm text-slate-dim">
            {processing
              ? `${finishedCount} of ${documents.length} documents finished`
              : `${classifiedCount} of ${documents.length} documents classified`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge tone={classifiedCount === documents.length && documents.length > 0 ? "success" : "warn"}>
            {classifiedCount}/{documents.length}
          </Badge>
          <Button
            variant="secondary"
            size="sm"
            disabled={processing || documents.length === 0}
            onClick={async () => {
              try {
                await startProcessing();
              } catch (err) {
                setError(err instanceof Error ? err.message : "Processing failed");
                setProcessing(false);
              }
            }}
          >
            {processing ? "Processing in background..." : "Process all in parallel"}
          </Button>
        </div>
      </div>

      {processing && (
        <div className="panel p-4 animate-fade-in">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate">
              Processing has started. This page refreshes document statuses every few seconds.
            </p>
            <Badge tone="info">{overallProgress}% done</Badge>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface">
            <div
              className="h-full rounded-full bg-gradient-to-r from-accent to-accent-glow transition-all duration-700"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Pack validation banner */}
      {documents.length > 0 && !processing && (
        <div className={`animate-fade-in panel p-4 ${packComplete ? "border-emerald/20" : "border-gold/20"}`}>
          <div className="flex items-start gap-3">
            <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${packComplete ? "bg-emerald/20 text-emerald-glow" : "bg-gold/20 text-gold-glow"}`}>
              {packComplete ? (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              ) : (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>
              )}
            </div>
            <div>
              <p className={`text-sm font-medium ${packComplete ? "text-emerald-glow" : "text-gold-glow"}`}>
                {packComplete
                  ? "Document pack complete — all 5 required categories are covered."
                  : `Document pack incomplete — ${missingCategories.length} category${missingCategories.length > 1 ? "ies" : "y"} missing for analysis.`}
              </p>
              {!packComplete && (
                <p className="mt-1 text-xs text-slate-dim">
                  Missing: {missingCategories.map((c) => c.replace(/_/g, " ")).join(", ")}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Classification cards */}
      <div className="grid gap-4">
        {sortedDocuments.map((document, index) => (
          <div
            key={document.id}
            className={`animate-slide-up stagger-${Math.min(index + 1, 6)} ${document.classification_status === "rejected" ? "opacity-60" : ""}`}
          >
            <ClassificationCard
              document={document}
              onApprove={async (category) => {
                await approveClassification(document.id, category);
                await refresh();
              }}
              onReject={async () => {
                await rejectClassification(document.id);
                await refresh();
              }}
            />
          </div>
        ))}

        {documents.length === 0 && (
          <div className="panel p-10 text-center animate-fade-in">
            <p className="text-sm text-slate-dim">No documents uploaded yet. Upload documents first.</p>
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="animate-fade-in panel border-rose/20 p-4">
          <span className="text-sm text-rose-glow">{error}</span>
        </div>
      )}
    </div>
  );
}
