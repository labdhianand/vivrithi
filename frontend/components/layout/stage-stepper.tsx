"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { getCase } from "@/lib/api";
import type { CaseRecord, CaseStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES = [
  { key: "onboarding", label: "Onboarding", description: "Entity and facility setup" },
  { key: "ingestion", label: "Ingestion", description: "Upload and classify documents" },
  { key: "extraction", label: "Extraction", description: "Review extracted fields" },
  { key: "analysis", label: "Analysis", description: "Research and scoring" },
  { key: "report", label: "Report", description: "Decision and CAM export" },
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
  if (pathname === "/onboarding") return "onboarding";
  if (/^\/cases\/[^/]+\/(upload|classify)(\/|$)/.test(pathname) || pathname === "/cases") return "ingestion";
  if (/^\/cases\/[^/]+\/(extraction|schema)(\/|$)/.test(pathname)) return "extraction";
  if (/^\/cases\/[^/]+\/analysis(\/|$)/.test(pathname)) return "analysis";
  if (/^\/cases\/[^/]+\/report(\/|$)/.test(pathname)) return "report";
  if (/^\/cases\/[^/]+(\/|$)/.test(pathname)) return "onboarding";
  return "onboarding";
}

function getStageHref(stageKey: StageKey, caseId: string | null): string | null {
  if (!caseId) {
    return stageKey === "onboarding" ? "/onboarding" : null;
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

export function StageStepper() {
  const pathname = usePathname();
  const [caseRecord, setCaseRecord] = useState<CaseRecord | null>(null);
  const caseId = useMemo(() => getCaseIdFromPath(pathname), [pathname]);
  const activeStage = useMemo(() => getStageFromPath(pathname), [pathname]);
  const activeStageIndex = STAGES.findIndex((stage) => stage.key === activeStage);
  const progressStageIndex = caseRecord ? STATUS_TO_STAGE_INDEX[caseRecord.status] : activeStageIndex;

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
    const intervalId = caseId ? window.setInterval(loadCase, 5000) : null;

    return () => {
      cancelled = true;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [caseId]);

  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-4 shadow-sm">
      <div className="overflow-x-auto">
        <div className="flex min-w-[720px] items-start justify-between gap-3">
          {STAGES.map((stage, index) => {
            const href = getStageHref(stage.key, caseId);
            const active = index === activeStageIndex;
            const completed = index < progressStageIndex;
            const locked = !active && !completed && index > progressStageIndex;
            const circleClass = active
              ? "bg-[#e91e8c] text-[#fce4ec]"
              : completed
                ? "bg-[#8b2252] text-[#fce4ec]"
                : "bg-[#3d1a2a] text-[#ad6883]";
            const labelClass = active || completed ? "text-[#fce4ec]" : "text-[#ad6883]";

            const content = (
              <div className="flex flex-1 items-start">
                <div className="flex min-w-[120px] flex-col items-center text-center">
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold transition-all duration-300",
                      circleClass,
                    )}
                  >
                    {completed ? (
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 10.5 8.5 14 15 6.5" />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </div>
                  <p className={cn("mt-3 text-sm font-semibold transition-all duration-300", labelClass)}>{stage.label}</p>
                  <p className="mt-1 text-xs text-[#ad6883]">{stage.description}</p>
                </div>
                {index < STAGES.length - 1 ? (
                  <div className="mt-5 flex-1 px-2">
                    <div
                      className={cn(
                        "h-1 rounded-full transition-all duration-300",
                        completed && index + 1 <= progressStageIndex ? "bg-[#e91e8c]" : "bg-[#4a1530]",
                      )}
                    />
                  </div>
                ) : null}
              </div>
            );

            if (!href || locked) {
              return <div key={stage.key} className="flex flex-1">{content}</div>;
            }

            return (
              <Link key={stage.key} href={href} className="flex flex-1">
                {content}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
