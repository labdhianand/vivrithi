"use client";

import { useEffect, useState } from "react";

import { getCrossChecks } from "@/lib/api";
import type { CrossCheck } from "@/lib/types";

function riskTone(item: CrossCheck) {
  const joined = `${item.check_name} ${item.note || ""}`.toLowerCase();
  if (joined.includes("critical") || joined.includes("(high)") || joined.includes("major credit quality concern")) {
    return { label: "High", className: "bg-red-100 text-red-700" };
  }
  if (joined.includes("(medium)") || joined.includes("elevated") || joined.includes("limited financial track record")) {
    return { label: "Medium", className: "bg-amber-100 text-amber-700" };
  }
  return { label: item.status === "match" ? "Positive" : "Review", className: item.status === "match" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700" };
}

export default function CrossCheckPage({ params }: { params: { caseId: string } }) {
  const [checks, setChecks] = useState<CrossCheck[]>([]);

  useEffect(() => {
    getCrossChecks(params.caseId).then(setChecks).catch(() => setChecks([]));
  }, [params.caseId]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Cross Verification</h1>
        <p className="mt-1 text-slate-500">Document triangulation and India-specific risk flags generated during analysis.</p>
      </div>

      <div className="space-y-4">
        {checks.map((item) => {
          const tone = riskTone(item);
          return (
            <div key={item.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-slate-900">{item.check_name}</h2>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${tone.className}`}>{tone.label}</span>
                  </div>
                  {item.note ? <p className="mt-3 text-sm leading-6 text-slate-600">{item.note}</p> : null}
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-lg bg-slate-50 px-4 py-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.doc_a || "Source A"}</p>
                      <p className="mt-1 text-sm text-slate-800">{item.value_a || "Not available"}</p>
                    </div>
                    <div className="rounded-lg bg-slate-50 px-4 py-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.doc_b || "Source B"}</p>
                      <p className="mt-1 text-sm text-slate-800">{item.value_b || "Not available"}</p>
                    </div>
                  </div>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">{item.status}</span>
              </div>
            </div>
          );
        })}
      </div>

      {checks.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">
          No cross-checks available. Run analysis first.
        </div>
      ) : null}
    </div>
  );
}
