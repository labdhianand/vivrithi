"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getCase } from "@/lib/api";
import type { CaseRecord, CaseStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES = [
  {
    key: "onboarding",
    label: "Onboarding",
    description: "Entity details and borrowing request",
  },
  {
    key: "ingestion",
    label: "Ingestion",
    description: "Upload and classify source documents",
  },
  {
    key: "extraction",
    label: "Extraction",
    description: "Review parsed fields and evidence",
  },
  {
    key: "analysis",
    label: "Analysis",
    description: "Research, scoring, and decision logic",
  },
  {
    key: "report",
    label: "Report",
    description: "Generate and export the final CAM",
  },
] as const;

type StageKey = (typeof STAGES)[number]["key"];

const STATUS_TO_STAGE_INDEX: Record<CaseStatus, number> = {
  onboarding: 0,
  documents_uploaded: 1,
  extracting: 2,
  extracted: 2,
  analyzing: 3,
  report_ready: 4,
};

function getCaseIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/cases\/([^/]+)/);
  return match?.[1] || null;
}

function getStageFromPath(pathname: string): StageKey {
  if (pathname === "/onboarding") {
    return "onboarding";
  }
  if (/^\/cases\/[^/]+\/(upload|classify)(\/|$)/.test(pathname) || pathname === "/cases") {
    return "ingestion";
  }
  if (/^\/cases\/[^/]+\/(extraction|schema)(\/|$)/.test(pathname)) {
    return "extraction";
  }
  if (/^\/cases\/[^/]+\/analysis(\/|$)/.test(pathname)) {
    return "analysis";
  }
  if (/^\/cases\/[^/]+\/report(\/|$)/.test(pathname)) {
    return "report";
  }
  if (/^\/cases\/[^/]+(\/|$)/.test(pathname)) {
    return "onboarding";
  }
  return "ingestion";
}

function getStageHref(stageKey: StageKey, caseId: string | null): string | null {
  if (!caseId) {
    if (stageKey === "onboarding") {
      return "/onboarding";
    }
    if (stageKey === "ingestion") {
      return "/cases";
    }
    return null;
  }

  switch (stageKey) {
    case "onboarding":
      return `/cases/${caseId}`;
    case "ingestion":
      return `/cases/${caseId}/upload`;
    case "extraction":
      return `/cases/${caseId}/extraction`;
    case "analysis":
      return `/cases/${caseId}/analysis`;
    case "report":
      return `/cases/${caseId}/report`;
    default:
      return null;
  }
}

function stageTone(active: boolean, completed: boolean, enabled: boolean) {
  if (active) {
    return {
      container: "border-accent/25 bg-accent/12 text-accent-glow shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]",
      badge: "bg-accent text-surface",
    };
  }
  if (completed) {
    return {
      container: "border-emerald/18 bg-emerald/10 text-emerald-glow",
      badge: "bg-emerald/20 text-emerald",
    };
  }
  if (enabled) {
    return {
      container: "border-white/[0.08] bg-surface-200/35 text-slate hover:border-white/[0.14] hover:bg-surface-200/70",
      badge: "bg-white/[0.08] text-slate-dim",
    };
  }
  return {
    container: "border-white/[0.04] bg-surface-200/20 text-slate-dim/60",
    badge: "bg-white/[0.04] text-slate-dim/60",
  };
}

export function StageStepper() {
  const pathname = usePathname();
  const [caseRecord, setCaseRecord] = useState<CaseRecord | null>(null);

  const caseId = useMemo(() => getCaseIdFromPath(pathname), [pathname]);
  const activeStage = useMemo(() => getStageFromPath(pathname), [pathname]);
  const activeStageIndex = STAGES.findIndex((stage) => stage.key === activeStage);

  useEffect(() => {
    let cancelled = false;

    async function loadCase() {
      if (!caseId) {
        setCaseRecord(null);
        return;
      }

      try {
        const nextCase = await getCase(caseId);
        if (!cancelled) {
          setCaseRecord(nextCase);
        }
      } catch {
        if (!cancelled) {
          setCaseRecord(null);
        }
      }
    }

    loadCase();
    if (!caseId) {
      return () => {
        cancelled = true;
      };
    }

    const timer = window.setInterval(loadCase, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [caseId, pathname]);

  const progressStageIndex = caseRecord ? STATUS_TO_STAGE_INDEX[caseRecord.status] : activeStageIndex;
  const currentStageMeta = STAGES[activeStageIndex] || STAGES[1];

  return (
    <div className="panel overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-4 py-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-dim">Journey</p>
          <p className="mt-1 text-sm text-slate">
            Blue is the current page. Green means the stage is already completed for this case.
          </p>
        </div>
        <div className="rounded-full border border-white/[0.08] bg-surface-200/60 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-dim">
          {currentStageMeta.label}: {currentStageMeta.description}
        </div>
      </div>

      <div className="overflow-x-auto px-3 pb-3 pt-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div className="flex min-w-max flex-nowrap gap-2">
        {STAGES.map((stage, index) => {
          const href = getStageHref(stage.key, caseId);
          const active = stage.key === activeStage;
          const completed = !active && index <= progressStageIndex;
          const enabled = Boolean(href);
          const tone = stageTone(active, completed, enabled);
          const content = (
            <>
              <span
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[11px] font-bold transition-colors",
                  tone.badge,
                )}
              >
                {completed ? (
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path
                      d="M2.5 6l2.5 2.5 4.5-5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  index + 1
                )}
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold">{stage.label}</span>
                <span className="block text-[11px] text-current/70">{stage.description}</span>
              </span>
            </>
          );

          if (!href) {
            return (
              <div
                key={stage.key}
                aria-disabled="true"
                className={cn(
                  "flex w-[220px] shrink-0 items-center gap-3 rounded-2xl border px-4 py-3 transition-all duration-200",
                  tone.container,
                )}
              >
                {content}
              </div>
            );
          }

          return (
            <Link
              key={stage.key}
              href={href}
              title={`Go to ${stage.label}`}
              className={cn(
                "flex w-[220px] shrink-0 items-center gap-3 rounded-2xl border px-4 py-3 transition-all duration-200",
                tone.container,
              )}
            >
              {content}
            </Link>
          );
        })}
        </div>
      </div>
    </div>
  );
}
