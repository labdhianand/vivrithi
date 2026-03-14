"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listCases } from "@/lib/api";
import type { CaseRecord } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const statusTone: Record<string, "default" | "success" | "warn" | "danger" | "info" | "neutral"> = {
  onboarding: "neutral",
  documents_uploaded: "info",
  extracting: "warn",
  extracted: "default",
  analyzing: "warn",
  report_ready: "success",
};

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCases().then(setCases).catch((err) => setError(err.message));
  }, []);

  return (
    <div className="space-y-5">
      {/* Hero */}
      <Card glow className="relative overflow-hidden">
        <div className="absolute inset-0 bg-mesh-gradient opacity-60" />
        <div className="relative grid gap-8 lg:grid-cols-[1.4fr_0.6fr]">
          <div className="space-y-5">
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-glow-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-accent/70">
                AI-Powered Credit Intelligence
              </span>
            </div>
            <h2 className="font-serif text-4xl leading-[1.15] text-slate-bright lg:text-5xl">
              From raw disclosures to<br />
              <span className="text-gradient">investment-grade CAMs</span>
            </h2>
            <p className="max-w-xl text-sm leading-relaxed text-slate-dim">
              Automated onboarding, intelligent document parsing, schema-guided extraction,
              ML-backed Five Cs scoring, and explainable credit recommendations — all in one path.
            </p>
            <div className="flex gap-3 pt-1">
              <Link href="/onboarding">
                <Button size="lg">Start New Case</Button>
              </Link>
              <Link href="/cases">
                <Button variant="secondary" size="lg">Open Pipeline</Button>
              </Link>
            </div>
          </div>

          {/* Quick stats */}
          <div className="flex flex-col justify-center gap-3">
            <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-4">
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-dim">Active Cases</div>
              <div className="mt-1 text-3xl font-bold text-gradient">{cases.length}</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-dim">Analyzing</div>
                <div className="mt-1 text-xl font-bold text-gold-glow">
                  {cases.filter((c) => c.status === "analyzing" || c.status === "extracting").length}
                </div>
              </div>
              <div className="rounded-xl border border-white/[0.06] bg-surface-200/60 p-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-dim">Reports</div>
                <div className="mt-1 text-xl font-bold text-emerald-glow">
                  {cases.filter((c) => c.status === "report_ready").length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Recent Cases */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Live Queue</div>
          <Link href="/cases" className="text-xs text-accent hover:text-accent-glow transition-colors">
            View all &rarr;
          </Link>
        </div>
        <div className="mt-4 space-y-2">
          {cases.slice(0, 6).map((item, i) => (
            <Link
              key={item.id}
              href={`/cases/${item.id}`}
              className={`group flex items-center justify-between rounded-xl border border-transparent bg-surface-200/40 px-4 py-3.5 transition-all duration-200 hover:border-accent/15 hover:bg-surface-200 animate-slide-up stagger-${i + 1}`}
              style={{ opacity: 0 }}
            >
              <div>
                <div className="font-medium text-slate-bright group-hover:text-accent-glow transition-colors">
                  {item.company_name}
                </div>
                <div className="mt-0.5 text-xs text-slate-dim">
                  {item.sector || "Sector pending"} &middot; {item.loan_amount_crore ? `₹${item.loan_amount_crore} Cr` : "Loan TBD"}
                </div>
              </div>
              <Badge tone={statusTone[item.status] || "neutral"} pulse={item.status === "extracting" || item.status === "analyzing"}>
                {item.status.replace(/_/g, " ")}
              </Badge>
            </Link>
          ))}
          {cases.length === 0 && (
            <div className="py-8 text-center text-sm text-slate-dim">
              {error || "No cases created yet. Start a new case to begin."}
            </div>
          )}
        </div>
      </Card>

      {/* Capabilities Grid */}
      <div className="grid gap-3 md:grid-cols-3">
        {[
          {
            title: "Document Intelligence",
            desc: "Parse PDFs, scanned tables, and financial disclosures with LLM-backed OCR and schema-guided extraction.",
            color: "accent",
          },
          {
            title: "Research Agent",
            desc: "Auto-crawl MCA filings, e-Courts, regulatory actions, and market data for 360-degree due diligence.",
            color: "gold",
          },
          {
            title: "ML Risk Engine",
            desc: "Gradient Boosting classifier trained on credit profiles — explainable PD predictions with feature importance.",
            color: "emerald",
          },
        ].map((cap, i) => (
          <Card key={cap.title} className={`animate-slide-up stagger-${i + 1}`} style={{ opacity: 0 }}>
            <div className={`h-1 w-10 rounded-full mb-4 ${cap.color === "accent" ? "bg-accent" : cap.color === "gold" ? "bg-gold" : "bg-emerald"}`} />
            <h3 className="text-sm font-semibold text-slate-bright">{cap.title}</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-dim">{cap.desc}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
