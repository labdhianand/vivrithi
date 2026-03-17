"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getRecommendation, listResearch, listNotes, getCrossChecks, runAnalysis } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { RecommendationPanel } from "@/components/analysis/recommendation-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const sections = [
  {
    key: "research",
    label: "Research Findings",
    description: "AI-driven market intelligence, news sentiment, and risk signals",
    href: (id: string) => `/cases/${id}/analysis/research`,
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9 9 0 0 1 3 12c0-1.47.353-2.856.978-4.082" />
      </svg>
    ),
    color: "text-[#ff6bb5]",
    bgGlow: "group-hover:shadow-[0_0_40px_rgba(233,30,140,0.12)]",
  },
  {
    key: "notes",
    label: "Analyst Notes",
    description: "Qualitative observations from site visits, meetings, and field intel",
    href: (id: string) => `/cases/${id}/analysis/notes`,
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
      </svg>
    ),
    color: "text-[#ff6bb5]",
    bgGlow: "group-hover:shadow-[0_0_40px_rgba(233,30,140,0.12)]",
  },
  {
    key: "cross-check",
    label: "Cross Verification",
    description: "Automated consistency checks across uploaded documents",
    href: (id: string) => `/cases/${id}/analysis/cross-check`,
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
      </svg>
    ),
    color: "text-[#ff6bb5]",
    bgGlow: "group-hover:shadow-[0_0_40px_rgba(233,30,140,0.12)]",
  },
  {
    key: "five-cs",
    label: "Five Cs Scoring",
    description: "Character, Capacity, Capital, Collateral, Conditions deep-dive",
    href: (id: string) => `/cases/${id}/analysis/five-cs`,
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
    color: "text-[#ff6bb5]",
    bgGlow: "group-hover:shadow-[0_0_40px_rgba(233,30,140,0.12)]",
  },
];

export default function AnalysisOverviewPage({ params }: { params: { caseId: string } }) {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [counts, setCounts] = useState<Record<string, number>>({});

  const refresh = () => getRecommendation(params.caseId).then(setRecommendation).catch(() => setRecommendation(null));

  useEffect(() => {
    refresh();
    // Fetch counts for each section
    listResearch(params.caseId).then((r) => setCounts((prev) => ({ ...prev, research: r.length }))).catch(() => {});
    listNotes(params.caseId).then((n) => setCounts((prev) => ({ ...prev, notes: n.length }))).catch(() => {});
    getCrossChecks(params.caseId).then((c) => setCounts((prev) => ({ ...prev, "cross-check": c.length }))).catch(() => {});
  }, [params.caseId]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Stage 4</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Pre-cognitive Analysis</h2>
            <p className="mt-1 text-sm text-slate">Run AI-powered credit analysis across all uploaded documents</p>
          </div>
          <Button
            disabled={busy}
            onClick={async () => {
              try {
                setBusy(true);
                setError(null);
                setRecommendation(await runAnalysis(params.caseId));
              } catch (err) {
                setError(err instanceof Error ? err.message : "Analysis failed");
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
                Running analysis...
              </>
            ) : (
              "Run Analysis"
            )}
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="panel p-5 border-rose/30 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-rose/15">
              <svg className="h-4 w-4 text-rose-glow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
            </div>
            <p className="text-sm text-rose-glow">{error}</p>
          </div>
        </div>
      )}

      {/* Recommendation summary */}
      {recommendation && (
        <div className="animate-fade-in">
          <RecommendationPanel recommendation={recommendation} caseId={params.caseId} />
        </div>
      )}

      {/* Section cards grid */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {sections.map((section, i) => (
          <Link
            key={section.key}
            href={section.href(params.caseId)}
            className={`group panel border-[#4a1530] p-5 transition-all duration-300 hover:border-[#7a2550] hover:bg-[#2d1420] ${section.bgGlow} animate-slide-up stagger-${i + 1}`}
          >
            <div className="flex items-start justify-between">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-[#3d1a2a] ${section.color}`}>
                {section.icon}
              </div>
              {counts[section.key] !== undefined && (
                <Badge tone="neutral">{counts[section.key]}</Badge>
              )}
            </div>
            <h3 className="mt-4 text-sm font-semibold text-slate-bright">{section.label}</h3>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-dim">{section.description}</p>
            <div className={`mt-4 flex items-center gap-1 text-xs font-medium ${section.color} opacity-0 transition-opacity duration-200 group-hover:opacity-100`}>
              <span>Explore</span>
              <svg className="h-3 w-3 transition-transform duration-200 group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
