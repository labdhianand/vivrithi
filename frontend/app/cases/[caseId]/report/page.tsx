"use client";

import { useEffect, useState } from "react";

import { generateReport, listReports } from "@/lib/api";
import type { ReportRecord } from "@/lib/types";
import { CamPreview } from "@/components/report/cam-preview";
import { DownloadButtons } from "@/components/report/download-buttons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function ReportPage({ params }: { params: { caseId: string } }) {
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [busy, setBusy] = useState(false);

  const refresh = () => listReports(params.caseId).then(setReports).catch(() => setReports([]));

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  const latest = reports[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Stage 5</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Credit Appraisal Memo</h2>
            <p className="mt-1 text-sm text-slate">
              Generate and export the comprehensive credit appraisal report
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await generateReport(params.caseId);
                  await refresh();
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Generating...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                  </svg>
                  Generate CAM
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Download bar */}
      {latest && (
        <div className="panel p-5 animate-slide-up stagger-1">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15">
                <svg className="h-5 w-5 text-accent-glow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-bright">Report ready</p>
                <p className="text-[11px] text-slate-dim">
                  Generated {new Date(latest.created_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
            <DownloadButtons reportId={latest.id} />
          </div>
        </div>
      )}

      {/* Report versions */}
      {reports.length > 1 && (
        <div className="panel p-5 animate-slide-up stagger-2">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim mb-3">Report History</p>
          <div className="space-y-2">
            {reports.map((r, i) => (
              <div
                key={r.id}
                className={`flex items-center justify-between rounded-xl px-4 py-2.5 text-sm ${
                  i === 0 ? "bg-accent/10 text-accent-glow" : "bg-surface-200 text-slate"
                }`}
              >
                <div className="flex items-center gap-2">
                  {i === 0 && <Badge tone="default">Latest</Badge>}
                  <span>{r.report_type}</span>
                </div>
                <span className="text-[11px] text-slate-dim">
                  {new Date(r.created_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preview or empty state */}
      {latest ? (
        <div className="animate-slide-up stagger-3">
          <CamPreview report={latest} />
        </div>
      ) : (
        <div className="panel p-5 text-center animate-fade-in">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-200">
            <svg className="h-8 w-8 text-slate-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <p className="mt-4 text-sm font-medium text-slate-bright">No report generated yet</p>
          <p className="mt-1 text-xs text-slate-dim">Click "Generate CAM" to create the credit appraisal memo</p>
        </div>
      )}
    </div>
  );
}
