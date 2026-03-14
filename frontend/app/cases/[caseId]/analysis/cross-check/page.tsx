"use client";

import { useEffect, useState } from "react";

import { getCrossChecks } from "@/lib/api";
import type { CrossCheck } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

export default function CrossCheckPage({ params }: { params: { caseId: string } }) {
  const [checks, setChecks] = useState<CrossCheck[]>([]);

  useEffect(() => {
    getCrossChecks(params.caseId).then(setChecks).catch(() => setChecks([]));
  }, [params.caseId]);

  const matchCount = checks.filter((c) => c.status === "match").length;
  const mismatchCount = checks.filter((c) => c.status !== "match").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Verification</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Cross Verification</h2>
            <p className="mt-1 text-sm text-slate">
              Automated consistency checks between uploaded document data points
            </p>
          </div>
          {checks.length > 0 && (
            <div className="flex items-center gap-3">
              <Badge tone="success">{matchCount} matched</Badge>
              {mismatchCount > 0 && <Badge tone="danger" pulse>{mismatchCount} mismatch</Badge>}
            </div>
          )}
        </div>
      </div>

      {/* Summary bar */}
      {checks.length > 0 && (
        <div className="panel p-5 animate-slide-up stagger-1">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim mb-3">Verification Progress</p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-200">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-glow to-accent-glow transition-all duration-700"
              style={{ width: `${checks.length > 0 ? (matchCount / checks.length) * 100 : 0}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-slate-dim">
            <span>{matchCount} of {checks.length} checks passed</span>
            <span className="font-semibold text-slate-bright">{checks.length > 0 ? Math.round((matchCount / checks.length) * 100) : 0}%</span>
          </div>
        </div>
      )}

      {/* Empty state */}
      {checks.length === 0 && (
        <div className="panel p-5 text-center animate-fade-in">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-surface-200">
            <svg className="h-6 w-6 text-slate-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-slate-dim">No cross-checks available. Run analysis first to generate verification data.</p>
        </div>
      )}

      {/* Check cards */}
      <div className="space-y-3">
        {checks.map((item, i) => {
          const isMatch = item.status === "match";
          return (
            <div
              key={item.id}
              className={`panel p-5 transition-all duration-300 hover:border-white/[0.12] animate-slide-up stagger-${Math.min(i + 1, 6)}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  {/* Status icon + check name */}
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                        isMatch ? "bg-emerald/15" : "bg-rose/15"
                      }`}
                    >
                      {isMatch ? (
                        <svg className="h-4 w-4 text-emerald-glow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                        </svg>
                      ) : (
                        <svg className="h-4 w-4 text-rose-glow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                          </svg>
                      )}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-bright">{item.check_name}</h3>
                    </div>
                  </div>

                  {/* Document comparison */}
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl bg-surface-200 px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Source A</p>
                      <p className="mt-1 text-sm font-medium text-slate-bright">{item.doc_a || "Document A"}</p>
                      {item.value_a && <p className="mt-0.5 text-xs text-slate">{item.value_a}</p>}
                    </div>
                    <div className="rounded-xl bg-surface-200 px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Source B</p>
                      <p className="mt-1 text-sm font-medium text-slate-bright">{item.doc_b || "Document B"}</p>
                      {item.value_b && <p className="mt-0.5 text-xs text-slate">{item.value_b}</p>}
                    </div>
                  </div>

                  {/* Discrepancy note */}
                  {item.discrepancy && (
                    <div className="mt-3 rounded-xl border border-rose/20 bg-rose/[0.06] px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-rose-glow">Discrepancy</p>
                      <p className="mt-1 text-sm text-slate">{item.discrepancy}</p>
                    </div>
                  )}

                  {item.note && (
                    <p className="mt-3 text-sm leading-relaxed text-slate">{item.note}</p>
                  )}
                </div>

                <Badge tone={isMatch ? "success" : "danger"}>
                  {item.status}
                </Badge>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
