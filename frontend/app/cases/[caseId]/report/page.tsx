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
  const latestCreatedAt = latest
    ? new Date(latest.created_at).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="space-y-6">
      <div className="panel overflow-hidden p-0 animate-slide-up">
        <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Stage 5</p>
            <h2 className="mt-2 font-serif text-4xl leading-tight text-slate-bright">
              Report Review <span className="text-gradient">& Export</span>
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate">
              Generate the final Credit Appraisal Memo, review the narrative structure, and export the submission-ready
              DOCX or PDF.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/[0.06] bg-surface-200/50 p-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Latest Version</p>
                <p className="mt-2 text-lg font-semibold text-slate-bright">{latest ? "Available" : "Not generated"}</p>
              </div>
              <div className="rounded-2xl border border-white/[0.06] bg-surface-200/50 p-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Report Count</p>
                <p className="mt-2 text-lg font-semibold text-slate-bright">{reports.length}</p>
              </div>
              <div className="rounded-2xl border border-white/[0.06] bg-surface-200/50 p-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Sections</p>
                <p className="mt-2 text-lg font-semibold text-slate-bright">{latest?.sections?.length || 0}</p>
              </div>
            </div>
          </div>

          <div className="rounded-[24px] border border-white/[0.06] bg-surface-200/50 p-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Actions</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-bright">
              {latest ? "Regenerate or download the memo" : "Generate the first CAM draft"}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate">
              {latest
                ? `Latest report generated ${latestCreatedAt}. Re-run generation after analysis changes to refresh the final memo.`
                : 'A generated report will appear here once you click "Generate CAM".'}
            </p>

            <div className="mt-5 flex flex-col gap-3">
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
                    {latest ? "Regenerate CAM" : "Generate CAM"}
                  </>
                )}
              </Button>

              {latest ? (
                <div className="rounded-2xl border border-white/[0.06] bg-surface-100/60 p-3">
                  <DownloadButtons reportId={latest.id} />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {reports.length > 0 && (
        <div className="panel p-5 animate-slide-up stagger-1">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Report History</p>
              <h3 className="mt-2 text-lg font-semibold text-slate-bright">Generated Versions</h3>
            </div>
            <div className="rounded-full border border-white/[0.08] bg-surface-200/60 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-dim">
              {reports.length} saved
            </div>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {reports.map((r, i) => (
              <div
                key={r.id}
                className={`rounded-2xl border px-4 py-3 ${
                  i === 0
                    ? "border-accent/20 bg-accent/10"
                    : "border-white/[0.06] bg-surface-200/50"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {i === 0 ? <Badge tone="default">Latest</Badge> : null}
                    <p className="text-sm font-medium text-slate-bright">{r.report_type.toUpperCase()}</p>
                  </div>
                  <p className="text-[11px] text-slate-dim">
                    {new Date(r.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <p className="mt-2 text-xs text-slate-dim">
                  {r.sections?.length || 0} section{(r.sections?.length || 0) !== 1 ? "s" : ""} in memo draft
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {latest ? (
        <div className="animate-slide-up stagger-2">
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
