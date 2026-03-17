"use client";

import { useState } from "react";
import type { CScore } from "@/lib/types";
import { EvidencePills } from "@/components/evidence/evidence-pills";

/* ------------------------------------------------------------------ */
/*  Score Card  –  individual C score with factor list                */
/* ------------------------------------------------------------------ */

function barColor(score: number) {
  if (score >= 70) return { bar: "#10b981", glow: "#34d399", bg: "rgba(16, 185, 129, 0.10)" };
  if (score >= 50) return { bar: "#f59e0b", glow: "#fbbf24", bg: "rgba(245, 158, 11, 0.10)" };
  return { bar: "#f43f5e", glow: "#fb7185", bg: "rgba(244, 63, 94, 0.10)" };
}

function badgeClasses(score: number) {
  if (score >= 70) return "bg-emerald/15 text-emerald-glow border-emerald/20";
  if (score >= 50) return "bg-gold/15 text-gold-glow border-gold/20";
  return "bg-rose/15 text-rose-glow border-rose/20";
}

export function ScoreCard({ label, score, caseId }: { label: string; score: CScore; caseId: string }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const colors = barColor(score.score);

  return (
    <div className="panel animate-slide-up border-[#4a1530] bg-[#1f0d16] p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Credit Factor
          </div>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">{label}</h3>
        </div>
        <div
          className={`flex items-center rounded-lg border px-2.5 py-1 text-sm font-bold tabular-nums ${badgeClasses(score.score)}`}
        >
          {score.score}<span className="ml-0.5 text-[10px] font-normal opacity-60">/100</span>
        </div>
      </div>

      {/* Progress bar */}
        <div className="mt-4">
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-surface-300/60">
            <div
              className="absolute inset-y-0 left-0 rounded-full blur-sm"
              style={{
                width: `${score.score}%`,
                backgroundColor: colors.glow,
                opacity: 0.4,
              }}
            />
            <div
              className="relative h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${score.score}%`,
                background: `linear-gradient(90deg, ${colors.bar}, ${colors.glow})`,
              }}
            />
          </div>
          <div className="mt-1.5 flex justify-between px-0.5">
            {[0, 25, 50, 75, 100].map((tick) => (
              <span key={tick} className="text-[8px] tabular-nums text-slate-dim/60">
                {tick}
              </span>
            ))}
          </div>
        </div>

      <p className="mt-3 text-[13px] leading-relaxed text-slate">{score.summary}</p>

      <div className="mt-4 space-y-1.5">
        <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
          Signals
        </div>
        {score.factors.map((factor, index) => {
          const isPositive = factor.impact >= 0;
          const isExpanded = expandedIdx === index;

          return (
            <button
              key={`${factor.signal}-${index}`}
              type="button"
              onClick={() => setExpandedIdx(isExpanded ? null : index)}
              className="group w-full cursor-pointer rounded-xl border border-[#4a1530] bg-[#2d1420]/70 px-3.5 py-2.5 text-left transition-colors hover:border-[#7a2550] hover:bg-[#2d1420]"
            >
              <div className="flex items-start gap-2.5">
                <div
                  className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-[11px] font-bold"
                  style={{
                    backgroundColor: isPositive
                      ? "rgba(16, 185, 129, 0.15)"
                      : "rgba(244, 63, 94, 0.15)",
                    color: isPositive ? "#34d399" : "#fb7185",
                  }}
                >
                  {isPositive ? "+" : "\u2212"}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-medium text-slate-bright">
                    {factor.signal}
                  </div>
                  {isExpanded && (
                    <div className="mt-1.5 animate-fade-in">
                      <div className="text-[12px] leading-relaxed text-slate/80">
                        {factor.evidence}
                      </div>
                      <EvidencePills refs={factor.evidence_refs} caseId={caseId} />
                    </div>
                  )}
                </div>
                <svg
                  className={`mt-1 h-3.5 w-3.5 shrink-0 text-slate-dim transition-transform duration-200 ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                  viewBox="0 0 16 16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M4 6l4 4 4-4" />
                </svg>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
