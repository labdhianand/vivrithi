"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getCase, listDocuments } from "@/lib/api";
import type { CaseRecord, DocumentRecord } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const statusTone: Record<string, "default" | "success" | "warn" | "danger" | "info" | "neutral"> = {
  onboarding: "neutral",
  documents_uploaded: "info",
  extracting: "warn",
  extracted: "default",
  analyzing: "warn",
  report_ready: "success",
};

const processingTone: Record<string, "default" | "success" | "warn" | "danger" | "info" | "neutral"> = {
  pending: "neutral",
  processing: "warn",
  classified: "info",
  completed: "success",
  extracted: "success",
  extraction_failed: "warn",
  failed: "danger",
};

function StatBlock({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 transition-colors duration-200 hover:border-[#7a2550] hover:bg-[#2d1420]">
      <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">{label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-bright">
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-slate-dim">{unit}</span>}
      </div>
    </div>
  );
}

export default function CaseOverviewPage({ params }: { params: { caseId: string } }) {
  const caseId = params?.caseId ?? "";
  const [record, setRecord] = useState<CaseRecord | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadCaseOverview() {
      if (!caseId) {
        setRecord(null);
        setDocuments([]);
        setError("Case not found.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const nextRecord = await getCase(caseId);
        if (!cancelled) {
          setRecord(nextRecord);
        }
      } catch (err) {
        if (!cancelled) {
          setRecord(null);
          setDocuments([]);
          setError(err instanceof Error ? err.message : "Failed to load case.");
          setLoading(false);
        }
        return;
      }

      try {
        const nextDocuments = await listDocuments(caseId);
        if (!cancelled) {
          setDocuments(nextDocuments);
        }
      } catch {
        if (!cancelled) {
          setDocuments([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCaseOverview();
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
        <span className="ml-3 text-sm text-slate-dim">Loading case...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card glow className="space-y-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Case Overview</div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-bright">Unable to load this case</h2>
          <p className="mt-2 text-sm text-slate-dim">{error}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" onClick={() => window.location.reload()}>
            Retry
          </Button>
          <Link href="/cases">
            <Button type="button" variant="secondary">Back to cases</Button>
          </Link>
        </div>
      </Card>
    );
  }

  if (!record) {
    return (
      <Card glow className="space-y-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Case Overview</div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-bright">Case not found</h2>
          <p className="mt-2 text-sm text-slate-dim">
            The case could not be loaded. It may have been deleted or the link is invalid.
          </p>
        </div>
        <Link href="/cases">
          <Button type="button">Back to cases</Button>
        </Link>
      </Card>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <Card glow className="animate-slide-up space-y-6">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Case Overview</div>
          <h2 className="text-gradient mt-2 font-serif text-3xl">{record.company_name || "Untitled Case"}</h2>
          {record.status && (
            <div className="mt-3">
              <Badge
                tone={statusTone[record.status] ?? "neutral"}
                pulse={record.status === "extracting" || record.status === "analyzing"}
              >
                {record.status.replaceAll("_", " ")}
              </Badge>
            </div>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="animate-fade-in stagger-1">
            <StatBlock label="Sector" value={record.sector || "N/A"} />
          </div>
          <div className="animate-fade-in stagger-2">
            <StatBlock label="Subsector" value={record.subsector || "N/A"} />
          </div>
          <div className="animate-fade-in stagger-3">
            <StatBlock label="Loan amount" value={record.loan_amount_crore || "N/A"} unit="Cr" />
          </div>
          <div className="animate-fade-in stagger-4">
            <StatBlock label="Documents" value={String(documents.length)} />
          </div>
        </div>

        <div className="flex gap-3 border-t border-[#4a1530] pt-5">
          <Link href={`/cases/${caseId}/upload`}>
            <Button>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="mr-1">
                <path d="M7 11V3M4 6l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              Upload documents
            </Button>
          </Link>
          <Link href={`/cases/${caseId}/analysis`}>
            <Button variant="secondary">Open analysis</Button>
          </Link>
        </div>
      </Card>

      <Card className="animate-slide-up stagger-2">
        <div className="flex items-center justify-between">
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Document Inventory</div>
          <span className="text-xs text-slate-dim">{documents.length} file{documents.length !== 1 && "s"}</span>
        </div>

        <div className="mt-4 space-y-2">
          {documents.length === 0 && (
            <div className="rounded-xl border border-dashed border-[#4a1530] py-10 text-center">
              <p className="text-sm text-slate-dim">No documents uploaded yet.</p>
              <Link
                href={`/cases/${caseId}/upload`}
                className="mt-2 inline-block text-xs text-accent transition-colors hover:text-accent-glow"
              >
                Upload your first document
              </Link>
            </div>
          )}
          {documents.map((item, idx) => (
            <div
              key={item.id}
              className={`animate-fade-in stagger-${Math.min(idx + 1, 6)} group flex items-start justify-between rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 transition-all duration-200 hover:border-[#7a2550] hover:bg-[#2d1420]`}
            >
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium text-sm text-slate-bright group-hover:text-accent-glow transition-colors">
                  {item.original_filename}
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-slate-dim">
                    {item.user_category || item.auto_category || "Uncategorized"}
                  </span>
                </div>
              </div>
              <Badge tone={processingTone[item.extraction_status || item.processing_status] ?? "neutral"} className="ml-3 shrink-0">
                {item.extraction_status || item.processing_status}
              </Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
