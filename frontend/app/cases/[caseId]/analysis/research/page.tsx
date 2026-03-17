"use client";

import { useEffect, useMemo, useState } from "react";

import { listResearch, runResearch } from "@/lib/api";
import type { ResearchItem } from "@/lib/types";
import { ResearchCard } from "@/components/research/research-card";

const SECTIONS = [
  { key: "news", label: "Company News" },
  { key: "legal", label: "Litigation & Legal" },
  { key: "promoter", label: "Promoter Background" },
  { key: "sector", label: "Sector Outlook" },
  { key: "mca", label: "MCA Company Data" },
] as const;

function bucketItems(items: ResearchItem[]) {
  const buckets: Record<string, ResearchItem[]> = {
    news: [],
    legal: [],
    promoter: [],
    sector: [],
    mca: [],
  };

  for (const item of items) {
    const source = `${item.source_name || ""} ${item.source_url || ""} ${item.title || ""}`.toLowerCase();
    if (source.includes("mca") || source.includes("zaubacorp")) {
      buckets.mca.push(item);
    } else if (item.category === "legal") {
      buckets.legal.push(item);
    } else if (item.category === "promoter") {
      buckets.promoter.push(item);
    } else if (item.category === "sector" || item.category === "regulatory" || item.category === "market") {
      buckets.sector.push(item);
    } else {
      buckets.news.push(item);
    }
  }

  return buckets;
}

function SkeletonSection() {
  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-5 shadow-card">
      <div className="h-4 w-32 animate-pulse rounded bg-[#3d1a2a]" />
      <div className="mt-4 space-y-3">
        <div className="h-24 animate-pulse rounded-lg bg-[#2d1420]" />
        <div className="h-24 animate-pulse rounded-lg bg-[#2d1420]" />
      </div>
    </div>
  );
}

export default function ResearchPage({ params }: { params: { caseId: string } }) {
  const [items, setItems] = useState<ResearchItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      setError(null);
      setItems(await listResearch(params.caseId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load research");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  const buckets = useMemo(() => bucketItems(items), [items]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 text-[#fce4ec]">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#fce4ec]">Research Findings</h1>
          <p className="mt-1 text-[#ad6883]">Firecrawl-only research grouped into the five appraisal categories.</p>
        </div>
        <button
          type="button"
          disabled={running}
          onClick={async () => {
            try {
              setRunning(true);
              setError(null);
              setItems(await runResearch(params.caseId));
            } catch (err) {
              setError(err instanceof Error ? err.message : "Research run failed");
            } finally {
              setRunning(false);
            }
          }}
          className="inline-flex items-center gap-2 rounded-lg bg-[#e91e8c] px-4 py-2 font-medium text-white transition-colors hover:bg-[#c4187a] disabled:opacity-50"
        >
          {running ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Running...
            </>
          ) : (
            "Run Research"
          )}
        </button>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      ) : null}

      {loading ? (
        <div className="space-y-4">
          {SECTIONS.map((section) => (
            <SkeletonSection key={section.key} />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {SECTIONS.map((section) => {
            const sectionItems = buckets[section.key];
            return (
              <section key={section.key} className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-5 shadow-card">
                <h2 className="text-xl font-semibold text-[#fce4ec]">{section.label}</h2>
                <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {sectionItems.length > 0 ? (
                    sectionItems.slice(0, 3).map((item) => <ResearchCard key={item.id} item={item} />)
                  ) : (
                    <div className="rounded-xl border border-[#4a1530] bg-[#2d1420] p-5 text-sm text-[#ad6883] shadow-card">
                      No Firecrawl findings available for this section yet.
                    </div>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
