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
  completed: "success",
  failed: "danger",
};

function StatBlock({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-surface-100 p-4 transition-colors duration-200 hover:border-white/[0.1]">
      <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">{label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-bright">
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-slate-dim">{unit}</span>}
      </div>
    </div>
  );
}

export default function CaseOverviewPage({ params }: { params: { caseId: string } }) {
  const [record, setRecord] = useState<CaseRecord | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getCase(params.caseId).then(setRecord),
      listDocuments(params.caseId).then(setDocuments).catch(() => setDocuments([])),
    ]).finally(() => setLoading(false));
  }, [params.caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
        <span className="ml-3 text-sm text-slate-dim">Loading case...</span>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      {/* Left column: Overview */}
      <Card glow className="animate-slide-up space-y-6">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Case Overview
          </div>
          <h2 className="text-gradient mt-2 font-serif text-3xl">
            {record?.company_name || "Untitled Case"}
          </h2>
          {record?.status && (
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
            <StatBlock label="Sector" value={record?.sector || "N/A"} />
          </div>
          <div className="animate-fade-in stagger-2">
            <StatBlock label="Subsector" value={record?.subsector || "N/A"} />
          </div>
          <div className="animate-fade-in stagger-3">
            <StatBlock label="Loan amount" value={record?.loan_amount_crore || "N/A"} unit="Cr" />
          </div>
          <div className="animate-fade-in stagger-4">
            <StatBlock label="Documents" value={String(documents.length)} />
          </div>
        </div>

        <div className="flex gap-3 border-t border-white/[0.06] pt-5">
          <Link href={`/cases/${params.caseId}/upload`}>
            <Button>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="mr-1">
                <path d="M7 11V3M4 6l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              Upload documents
            </Button>
          </Link>
          <Link href={`/cases/${params.caseId}/analysis`}>
            <Button variant="secondary">Open analysis</Button>
          </Link>
        </div>
      </Card>

      {/* Right column: Document inventory */}
      <Card className="animate-slide-up stagger-2">
        <div className="flex items-center justify-between">
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Document Inventory
          </div>
          <span className="text-xs text-slate-dim">{documents.length} file{documents.length !== 1 && "s"}</span>
        </div>

        <div className="mt-4 space-y-2">
          {documents.length === 0 && (
            <div className="rounded-xl border border-dashed border-white/[0.08] py-10 text-center">
              <p className="text-sm text-slate-dim">No documents uploaded yet.</p>
              <Link href={`/cases/${params.caseId}/upload`} className="mt-2 inline-block text-xs text-accent hover:text-accent-glow transition-colors">
                Upload your first document
              </Link>
            </div>
          )}
          {documents.map((item, idx) => (
            <div
              key={item.id}
              className={`animate-fade-in stagger-${Math.min(idx + 1, 6)} group flex items-start justify-between rounded-xl border border-white/[0.06] bg-surface-100 p-4 transition-all duration-200 hover:border-white/[0.1] hover:bg-surface-200`}
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
              <Badge tone={processingTone[item.processing_status] ?? "neutral"} className="ml-3 shrink-0">
                {item.processing_status}
              </Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
