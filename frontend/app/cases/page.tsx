"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listCases } from "@/lib/api";
import type { CaseRecord } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const statusTone: Record<string, "default" | "success" | "warn" | "danger" | "info" | "neutral"> = {
  onboarding: "neutral",
  documents_uploaded: "info",
  extracting: "warn",
  extracted: "default",
  analyzing: "warn",
  report_ready: "success",
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listCases()
      .then(setCases)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="animate-slide-up flex items-end justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Case Pipeline</div>
          <h1 className="text-gradient mt-2 font-serif text-3xl">Underwriting Cases</h1>
        </div>
        <Link href="/onboarding">
          <Button size="sm">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="mr-1">
              <path d="M7 1v12M1 7h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            New case
          </Button>
        </Link>
      </div>

      <Card glow className="animate-slide-up stagger-2 overflow-hidden border-[#4a1530] p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[#4a1530] bg-[#2d1420]/70">
                <th className="px-5 py-3.5 text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">Company</th>
                <th className="px-5 py-3.5 text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">Sector</th>
                <th className="px-5 py-3.5 text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">Status</th>
                <th className="px-5 py-3.5 text-right text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">
                  Loan Amount
                </th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item, idx) => (
                <tr
                  key={item.id}
                  className={`animate-fade-in border-b border-[#4a1530]/70 transition-colors duration-150 hover:bg-[#3d1a2a]/40 stagger-${Math.min(idx + 1, 6)}`}
                >
                  <td className="px-5 py-4">
                    <Link
                      href={`/cases/${item.id}`}
                      className="font-medium text-accent-glow transition-colors hover:text-accent"
                    >
                      {item.company_name}
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-slate">
                    {item.sector || <span className="text-slate-dim">--</span>}
                  </td>
                  <td className="px-5 py-4">
                    <Badge tone={statusTone[item.status] ?? "neutral"} pulse={item.status === "extracting" || item.status === "analyzing"}>
                      {item.status.replaceAll("_", " ")}
                    </Badge>
                  </td>
                  <td className="px-5 py-4 text-right font-medium text-slate-bright">
                    {item.loan_amount_crore ? (
                      <>{item.loan_amount_crore} <span className="text-xs text-slate-dim">Cr</span></>
                    ) : (
                      <span className="text-slate-dim">--</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
            <span className="ml-3 text-sm text-slate-dim">Loading cases...</span>
          </div>
        )}
        {!loading && cases.length === 0 && (
          <div className="py-16 text-center">
            <div className="text-slate-dim">
              {error ? (
                <span className="text-rose-glow">{error}</span>
              ) : (
                <>
                  <p className="text-base text-slate-bright">No cases yet</p>
                  <p className="mt-1 text-sm text-slate-dim">
                    Create your first underwriting case to get started.
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
