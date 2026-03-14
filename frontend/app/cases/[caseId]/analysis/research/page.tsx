"use client";

import { useEffect, useState } from "react";

import { deleteResearchItem, listResearch, runResearch } from "@/lib/api";
import type { ResearchItem } from "@/lib/types";
import { ResearchCard } from "@/components/research/research-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function ResearchPage({ params }: { params: { caseId: string } }) {
  const [items, setItems] = useState<ResearchItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState<string>("all");

  const refresh = () => listResearch(params.caseId).then(setItems).catch(() => setItems([]));

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  const categories = Array.from(new Set(items.map((i) => i.category))).filter(Boolean);

  const filtered = filter === "all" ? items : items.filter((i) => i.category === filter);

  const sentimentCounts = {
    positive: items.filter((i) => i.sentiment === "positive").length,
    negative: items.filter((i) => i.sentiment === "negative").length,
    neutral: items.filter((i) => i.sentiment !== "positive" && i.sentiment !== "negative").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Research</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Research Findings</h2>
            <p className="mt-1 text-sm text-slate">
              AI-curated intelligence from public sources, news, and regulatory filings
            </p>
          </div>
          <Button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                setItems(await runResearch(params.caseId));
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
                Researching...
              </>
            ) : (
              "Run Research"
            )}
          </Button>
        </div>
      </div>

      {/* Stats row */}
      {items.length > 0 && (
        <div className="grid grid-cols-3 gap-4 animate-slide-up stagger-1">
          <div className="panel p-5 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Positive</p>
            <p className="mt-2 text-2xl font-bold text-emerald-glow">{sentimentCounts.positive}</p>
          </div>
          <div className="panel p-5 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Negative</p>
            <p className="mt-2 text-2xl font-bold text-rose-glow">{sentimentCounts.negative}</p>
          </div>
          <div className="panel p-5 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Neutral</p>
            <p className="mt-2 text-2xl font-bold text-slate">{sentimentCounts.neutral}</p>
          </div>
        </div>
      )}

      {/* Category filters */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 animate-slide-up stagger-2">
          <button
            onClick={() => setFilter("all")}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium uppercase tracking-wider transition-all duration-200 ${
              filter === "all"
                ? "border-accent/40 bg-accent/15 text-accent-glow"
                : "border-white/[0.08] bg-surface-200 text-slate-dim hover:text-slate hover:border-white/[0.12]"
            }`}
          >
            All ({items.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium uppercase tracking-wider transition-all duration-200 ${
                filter === cat
                  ? "border-accent/40 bg-accent/15 text-accent-glow"
                  : "border-white/[0.08] bg-surface-200 text-slate-dim hover:text-slate hover:border-white/[0.12]"
              }`}
            >
              {cat} ({items.filter((i) => i.category === cat).length})
            </button>
          ))}
        </div>
      )}

      {/* Research cards */}
      {filtered.length === 0 && !busy && (
        <div className="panel p-5 text-center animate-fade-in">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-surface-200">
            <svg className="h-6 w-6 text-slate-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9 9 0 0 1 3 12c0-1.47.353-2.856.978-4.082" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-slate-dim">No research findings yet. Run research to begin.</p>
        </div>
      )}

      <div className="space-y-4">
        {filtered.map((item, i) => (
          <div key={item.id} className={`animate-slide-up stagger-${Math.min(i + 1, 6)}`}>
            <ResearchCard
              item={item}
              onDelete={async () => {
                await deleteResearchItem(item.id);
                await refresh();
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
