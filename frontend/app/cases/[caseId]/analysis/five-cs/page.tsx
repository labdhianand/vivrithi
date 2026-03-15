"use client";

import { useEffect, useState } from "react";

import { getAnalysisSummary, getFiveCs, getRecommendation, getSwot } from "@/lib/api";
import type { AnalysisSummary, FiveCs, Recommendation, SWOT } from "@/lib/types";
import { AnalysisSummaryPanels } from "@/components/analysis/analysis-summary-panels";
import { FiveCsRadar } from "@/components/analysis/five-cs-radar";
import { RecommendationPanel } from "@/components/analysis/recommendation-panel";
import { ScoreCard } from "@/components/analysis/score-card";
import { SwotGrid } from "@/components/analysis/swot-grid";
import { Badge } from "@/components/ui/badge";

const cMeta: Record<string, { color: string; icon: React.ReactNode }> = {
  Character: {
    color: "text-accent-glow",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
      </svg>
    ),
  },
  Capacity: {
    color: "text-emerald-glow",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
      </svg>
    ),
  },
  Capital: {
    color: "text-gold-glow",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ),
  },
  Collateral: {
    color: "text-rose-glow",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
      </svg>
    ),
  },
  Conditions: {
    color: "text-blue-400",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9 9 0 0 1 3 12c0-1.47.353-2.856.978-4.082" />
      </svg>
    ),
  },
};

function gradeColor(score: number): string {
  if (score >= 80) return "text-emerald-glow";
  if (score >= 60) return "text-gold-glow";
  if (score >= 40) return "text-accent-glow";
  return "text-rose-glow";
}

function gradeTone(score: number): "success" | "warn" | "info" | "danger" {
  if (score >= 80) return "success";
  if (score >= 60) return "warn";
  if (score >= 40) return "info";
  return "danger";
}

export default function FiveCsPage({ params }: { params: { caseId: string } }) {
  const [scores, setScores] = useState<FiveCs | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [swot, setSwot] = useState<SWOT | null>(null);
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);

  useEffect(() => {
    getFiveCs(params.caseId).then(setScores).catch(() => setScores(null));
    getRecommendation(params.caseId).then(setRecommendation).catch(() => setRecommendation(null));
    getSwot(params.caseId).then(setSwot).catch(() => setSwot(null));
    getAnalysisSummary(params.caseId).then(setSummary).catch(() => setSummary(null));
  }, [params.caseId]);

  if (!scores) {
    return (
      <div className="panel p-5 text-center animate-fade-in">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-surface-200">
          <svg className="h-6 w-6 text-slate-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
        </div>
        <p className="mt-3 text-sm text-slate-dim">Run analysis first to populate Five Cs scoring.</p>
      </div>
    );
  }

  const cEntries: { label: string; score: typeof scores.character }[] = [
    { label: "Character", score: scores.character },
    { label: "Capacity", score: scores.capacity },
    { label: "Capital", score: scores.capital },
    { label: "Collateral", score: scores.collateral },
    { label: "Conditions", score: scores.conditions },
  ];

  return (
    <div className="space-y-6">
      {/* Header with overall score */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Credit Assessment</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Five Cs Analysis</h2>
            <p className="mt-1 text-sm text-slate">
              Comprehensive credit scoring across Character, Capacity, Capital, Collateral, and Conditions
            </p>
          </div>
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Overall</p>
            <p className={`mt-1 text-3xl font-bold ${gradeColor(scores.overall_score)}`}>{scores.overall_score}</p>
            <Badge tone={gradeTone(scores.overall_score)}>{scores.risk_grade}</Badge>
          </div>
        </div>
      </div>

      {/* Radar chart */}
      <div className="animate-slide-up stagger-1">
        <FiveCsRadar data={scores} />
      </div>

      {/* Score cards grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cEntries.map((entry, i) => {
          const meta = cMeta[entry.label];
          return (
            <div key={entry.label} className={`animate-slide-up stagger-${Math.min(i + 2, 6)}`}>
              <ScoreCard label={entry.label} score={entry.score} caseId={params.caseId} />
            </div>
          );
        })}
      </div>

      {/* Recommendation */}
      {recommendation && (
        <div className="animate-slide-up stagger-5">
          <RecommendationPanel recommendation={recommendation} caseId={params.caseId} />
        </div>
      )}

      {summary && (
        <div className="animate-slide-up stagger-6">
          <AnalysisSummaryPanels summary={summary} />
        </div>
      )}

      {/* ML Model Transparency */}
      {recommendation && (recommendation as any).ml_prediction?.model_metadata && (
        <div className="animate-slide-up stagger-6">
          <div className="panel p-5">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Model Transparency</p>
            <h3 className="mt-2 text-base font-semibold text-slate-bright">ML Risk Model Info</h3>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Training AUC</p>
                <p className="mt-1 text-lg font-semibold text-accent-glow">
                  {((recommendation as any).ml_prediction.model_metadata.training_auc * 100).toFixed(1)}%
                </p>
              </div>
              <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Model Type</p>
                <p className="mt-1 text-sm text-slate-bright">{(recommendation as any).ml_prediction.model_metadata.model_type}</p>
              </div>
              <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Training Samples</p>
                <p className="mt-1 text-sm text-slate-bright">{(recommendation as any).ml_prediction.model_metadata.training_samples}</p>
              </div>
            </div>
            {(recommendation as any).ml_prediction.model_metadata.top_features && (
              <div className="mt-4">
                <p className="text-xs font-medium text-slate-dim mb-2">Top Feature Importances</p>
                <div className="space-y-1.5">
                  {(recommendation as any).ml_prediction.model_metadata.top_features.slice(0, 5).map((f: any) => (
                    <div key={f.feature} className="flex items-center gap-3">
                      <span className="w-40 text-xs text-slate">{f.feature}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-surface overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-accent to-accent-glow" style={{ width: `${Math.min(f.importance * 3, 100)}%` }} />
                      </div>
                      <span className="text-xs text-slate-dim w-12 text-right">{f.importance}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="mt-4 text-xs text-slate-dim/80 leading-relaxed">
              {(recommendation as any).ml_prediction.model_metadata.calibration_disclaimer}
            </p>
          </div>
        </div>
      )}

      {/* SWOT */}
      {swot && (
        <div className="animate-slide-up stagger-6">
          <SwotGrid swot={swot} />
        </div>
      )}
    </div>
  );
}
