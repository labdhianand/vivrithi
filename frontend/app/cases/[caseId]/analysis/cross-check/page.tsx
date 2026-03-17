"use client";

import { useEffect, useState } from "react";

import { getCrossChecks } from "@/lib/api";
import type { CrossCheck } from "@/lib/types";

function riskTone(item: CrossCheck) {
  const joined = `${item.check_name} ${item.note || ""}`.toLowerCase();
  if (joined.includes("critical") || joined.includes("(high)") || joined.includes("major credit quality concern")) {
    return { label: "High", className: "bg-red-950 text-red-300" };
  }
  if (joined.includes("(medium)") || joined.includes("elevated") || joined.includes("limited financial track record")) {
    return { label: "Medium", className: "bg-amber-950 text-amber-300" };
  }
  return {
    label: item.status === "match" ? "Positive" : "Review",
    className: item.status === "match" ? "bg-green-950 text-green-300" : "bg-[#3d1a2a] text-[#f48fb1]",
  };
}

export default function CrossCheckPage({ params }: { params: { caseId: string } }) {
  const [checks, setChecks] = useState<CrossCheck[]>([]);

  useEffect(() => {
    getCrossChecks(params.caseId).then(setChecks).catch(() => setChecks([]));
  }, [params.caseId]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 text-[#fce4ec]">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fce4ec]">Cross Verification</h1>
        <p className="mt-1 text-[#ad6883]">Document triangulation and India-specific risk flags generated during analysis.</p>
      </div>

      <div className="space-y-4">
        {checks.map((item) => {
          const tone = riskTone(item);
          return (
            <div key={item.id} className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-5 shadow-card">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-[#fce4ec]">{item.check_name}</h2>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${tone.className}`}>{tone.label}</span>
                  </div>
                  {item.note ? <p className="mt-3 text-sm leading-6 text-[#f48fb1]">{item.note}</p> : null}
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <div className="rounded-lg border border-[#4a1530] bg-[#2d1420] px-4 py-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-[#ad6883]">{item.doc_a || "Source A"}</p>
                      <p className="mt-1 text-sm text-[#fce4ec]">{item.value_a || "Not available"}</p>
                    </div>
                    <div className="rounded-lg border border-[#4a1530] bg-[#2d1420] px-4 py-3">
                      <p className="text-xs font-medium uppercase tracking-wide text-[#ad6883]">{item.doc_b || "Source B"}</p>
                      <p className="mt-1 text-sm text-[#fce4ec]">{item.value_b || "Not available"}</p>
                    </div>
                  </div>
                </div>
                <span className="rounded-full border border-[#4a1530] bg-[#2d1420] px-3 py-1 text-sm font-medium text-[#f48fb1]">{item.status}</span>
              </div>
            </div>
          );
        })}
      </div>

      {checks.length === 0 ? (
        <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-8 text-center text-[#ad6883] shadow-card">
          No cross-checks available. Run analysis first.
        </div>
      ) : null}
    </div>
  );
}
