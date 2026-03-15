"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import {
  generateReport,
  getCrossChecks,
  getFiveCs,
  getRecommendation,
  getReportDownloadUrl,
  getSwot,
  listReports,
  listResearch,
} from "@/lib/api";
import { useWorkbenchStore } from "@/lib/store";
import { formatCurrency } from "@/lib/utils";
import type { CrossCheck, FiveCs, Recommendation, ReportRecord, ResearchItem, SWOT } from "@/lib/types";
import { ResearchCard } from "@/components/research/research-card";

const SECTION_LABELS = [
  { key: "news", label: "Company News" },
  { key: "legal", label: "Litigation & Legal" },
  { key: "promoter", label: "Promoter Background" },
  { key: "sector", label: "Sector Outlook" },
  { key: "mca", label: "MCA Company Data" },
] as const;

function decisionStyles(decision?: string | null) {
  if (decision === "approve") {
    return {
      wrapper: "bg-emerald-50 border-l-4 border-emerald-500",
      title: "APPROVED",
      titleClass: "text-3xl font-bold text-emerald-800",
    };
  }
  if (decision === "conditional_approve") {
    return {
      wrapper: "bg-amber-50 border-l-4 border-amber-500",
      title: "CONDITIONAL APPROVAL",
      titleClass: "text-3xl font-bold text-amber-800",
    };
  }
  return {
    wrapper: "bg-red-50 border-l-4 border-red-500",
    title: "REJECTED",
    titleClass: "text-3xl font-bold text-red-800",
  };
}

function scoreBadgeClass(score: number) {
  if (score > 70) return "bg-emerald-100 text-emerald-700";
  if (score >= 50) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
}

function bucketResearch(items: ResearchItem[]) {
  const buckets: Record<string, ResearchItem[]> = { news: [], legal: [], promoter: [], sector: [], mca: [] };
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

function placeholderResearch(caseId: string, category: string, title: string): ResearchItem {
  return {
    id: `${category}-placeholder`,
    case_id: caseId,
    category,
    title,
    summary: "No findings generated for this section yet.",
    severity: "low",
    created_at: new Date(0).toISOString(),
    updated_at: new Date(0).toISOString(),
  };
}

function flagTone(check: CrossCheck) {
  const text = `${check.check_name} ${check.note || ""}`.toLowerCase();
  if (text.includes("critical") || text.includes("(high)") || text.includes("major credit quality concern")) {
    return "bg-red-100 text-red-700";
  }
  if (text.includes("(medium)") || text.includes("elevated") || text.includes("limited financial track record")) {
    return "bg-amber-100 text-amber-700";
  }
  return check.status === "match" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700";
}

export default function ReportPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const resetWorkbench = useWorkbenchStore((state) => state.reset);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [fiveCs, setFiveCs] = useState<FiveCs | null>(null);
  const [swot, setSwot] = useState<SWOT | null>(null);
  const [research, setResearch] = useState<ResearchItem[]>([]);
  const [crossChecks, setCrossChecks] = useState<CrossCheck[]>([]);
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const [nextRecommendation, nextFiveCs, nextSwot, nextResearch, nextCrossChecks, nextReports] = await Promise.all([
        getRecommendation(params.caseId).catch(() => null),
        getFiveCs(params.caseId).catch(() => null),
        getSwot(params.caseId).catch(() => null),
        listResearch(params.caseId).catch(() => []),
        getCrossChecks(params.caseId).catch(() => []),
        listReports(params.caseId).catch(() => []),
      ]);
      setRecommendation(nextRecommendation);
      setFiveCs(nextFiveCs);
      setSwot(nextSwot);
      setResearch(nextResearch);
      setCrossChecks(nextCrossChecks);
      setReports(nextReports);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load report data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  const latestReport = reports[0] || null;
  const researchBuckets = useMemo(() => bucketResearch(research), [research]);
  const researchCards = SECTION_LABELS.map((section) => researchBuckets[section.key][0] || placeholderResearch(params.caseId, section.key, section.label));
  const radarData = fiveCs
    ? [
        { subject: "Character", score: fiveCs.character.score, fullMark: 100 },
        { subject: "Capacity", score: fiveCs.capacity.score, fullMark: 100 },
        { subject: "Capital", score: fiveCs.capital.score, fullMark: 100 },
        { subject: "Collateral", score: fiveCs.collateral.score, fullMark: 100 },
        { subject: "Conditions", score: fiveCs.conditions.score, fullMark: 100 },
      ]
    : [];

  if (loading) {
    return <div className="mx-auto max-w-5xl px-4 py-8 text-slate-500">Loading report dashboard...</div>;
  }

  if (!recommendation || !fiveCs || !swot) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Report Dashboard</h1>
          <p className="mt-3 text-slate-500">Run analysis first to populate the decision dashboard and CAM export.</p>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        </div>
      </div>
    );
  }

  const decision = decisionStyles(recommendation.recommendation);
  const reasoningParagraphs = recommendation.decision_reasoning
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="space-y-8">
        <section className={`rounded-xl p-6 shadow-sm ${decision.wrapper}`}>
          <div className={decision.titleClass}>{decision.title}</div>
          <p className="mt-3 text-lg text-slate-700">
            Recommended: {formatCurrency(recommendation.recommended_amount_crore)} at {recommendation.recommended_rate_percent || "N/A"}% p.a.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-white px-3 py-1 text-sm font-medium text-slate-800 shadow-sm">{recommendation.risk_grade}</span>
            <span className="text-sm font-medium text-slate-700">Score: {recommendation.overall_score}/100</span>
          </div>
          <div className="mt-4 space-y-3">
            {reasoningParagraphs.map((paragraph) => (
              <p key={paragraph} className="text-slate-700">
                {paragraph}
              </p>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Five Cs Radar</h2>
            <div className="mt-4 h-[350px]">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} />
                  <Radar dataKey="score" stroke="#2563EB" fill="#2563EB" fillOpacity={0.25} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-4">
            {[
              { label: "Character", score: fiveCs.character.score, summary: fiveCs.character.summary },
              { label: "Capacity", score: fiveCs.capacity.score, summary: fiveCs.capacity.summary },
              { label: "Capital", score: fiveCs.capital.score, summary: fiveCs.capital.summary },
              { label: "Collateral", score: fiveCs.collateral.score, summary: fiveCs.collateral.summary },
              { label: "Conditions", score: fiveCs.conditions.score, summary: fiveCs.conditions.summary },
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-900">{item.label}</h3>
                  <span className={`rounded-full px-3 py-1 text-sm font-medium ${scoreBadgeClass(item.score)}`}>{item.score}</span>
                </div>
                <p className="mt-3 text-sm text-slate-600">{item.summary}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold text-slate-900">SWOT Analysis</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              { title: "Strengths", items: swot.strengths, className: "bg-emerald-50 border-emerald-200 text-emerald-800" },
              { title: "Weaknesses", items: swot.weaknesses, className: "bg-red-50 border-red-200 text-red-800" },
              { title: "Opportunities", items: swot.opportunities, className: "bg-blue-50 border-blue-200 text-blue-800" },
              { title: "Threats", items: swot.threats, className: "bg-amber-50 border-amber-200 text-amber-800" },
            ].map((section) => (
              <div key={section.title} className={`rounded-xl border p-5 shadow-sm ${section.className}`}>
                <h3 className="font-semibold">{section.title}</h3>
                <ul className="mt-3 space-y-2 text-sm">
                  {section.items.length > 0 ? (
                    section.items.map((item, index) => <li key={`${section.title}-${index}`}>- {item.point}</li>)
                  ) : (
                    <li>No items available.</li>
                  )}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold text-slate-900">Research Findings</h2>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {researchCards.map((item) => (
              <ResearchCard key={item.id} item={item} />
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold text-slate-900">India Flags</h2>
          <div className="flex flex-wrap gap-3">
            {crossChecks.length > 0 ? (
              crossChecks.map((check) => (
                <span key={check.id} className={`rounded-full px-3 py-2 text-sm font-medium ${flagTone(check)}`}>
                  {check.note || check.check_name}
                </span>
              ))
            ) : (
              <span className="rounded-full bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-700">No India-specific flags raised.</span>
            )}
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Download</h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              disabled={downloading}
              onClick={async () => {
                try {
                  setDownloading(true);
                  const report = latestReport || (await generateReport(params.caseId));
                  if (!latestReport) {
                    await refresh();
                  }
                  window.location.assign(getReportDownloadUrl(report.id, "docx"));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed to download report");
                } finally {
                  setDownloading(false);
                }
              }}
              className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {downloading ? "Preparing report..." : "Download CAM Report"}
            </button>
            <button
              type="button"
              onClick={() => {
                resetWorkbench();
                router.push("/");
              }}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              Start New Application
            </button>
          </div>
          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
        </section>
      </div>
    </div>
  );
}
