"use client";

import { useState } from "react";

import type { DocumentRecord } from "@/lib/types";
import { DOCUMENT_CATEGORIES } from "@/lib/utils";

function badgeClass(category: string) {
  const key = category.toLowerCase();
  if (key.includes("annual")) return "bg-blue-50 text-blue-700";
  if (key.includes("share")) return "bg-amber-50 text-amber-700";
  if (key.includes("borrow")) return "bg-emerald-50 text-emerald-700";
  if (key.includes("portfolio")) return "bg-purple-50 text-purple-700";
  return "bg-slate-100 text-slate-700";
}

export function ClassificationCard({
  document,
  onApprove,
  onReject,
}: {
  document: DocumentRecord;
  onApprove: (category: string) => Promise<void>;
  onReject: () => Promise<void>;
}) {
  const [category, setCategory] = useState(document.user_category || document.auto_category || DOCUMENT_CATEGORIES[0]);
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);
  const confidence = Math.round(Number(document.auto_category_confidence || 0) * 100);
  const approved = ["approved", "user_approved"].includes(document.classification_status);
  const rejected = document.classification_status === "rejected";
  const reviewed = approved || rejected;

  return (
    <div
      className={`rounded-xl bg-white p-6 shadow-sm border border-slate-200 ${
        approved ? "border-l-4 border-emerald-500" : rejected ? "border-l-4 border-red-400 opacity-60" : ""
      }`}
    >
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="max-w-full truncate text-lg font-semibold text-slate-900">{document.original_filename}</h3>
            {approved ? (
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">Approved</span>
            ) : null}
            {rejected ? (
              <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">Rejected</span>
            ) : null}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${badgeClass(category)}`}>
              {(document.auto_category || category).replace(/_/g, " ")}
            </span>
            <span className="text-sm text-slate-600">Confidence {confidence}%</span>
          </div>

          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-blue-600 transition-all"
              style={{ width: `${Math.max(confidence, 4)}%` }}
            />
          </div>

          <p className="mt-3 text-sm text-slate-500">
            {document.auto_category
              ? `Predicted from layout signals and first-page content for ${(document.auto_category || "").replace(/_/g, " ")}.`
              : "Awaiting AI classification output."}
          </p>
        </div>

        {!reviewed ? (
          <div className="w-full max-w-sm space-y-3">
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {DOCUMENT_CATEGORIES.map((option) => (
                <option key={option} value={option}>
                  {option.replace(/_/g, " ")}
                </option>
              ))}
            </select>

            <div className="flex gap-3">
              <button
                type="button"
                disabled={busy !== null}
                onClick={async () => {
                  try {
                    setBusy("approve");
                    await onApprove(category);
                  } finally {
                    setBusy(null);
                  }
                }}
                className="flex-1 rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
              >
                {busy === "approve" ? "Saving..." : "Approve"}
              </button>
              <button
                type="button"
                disabled={busy !== null}
                onClick={async () => {
                  try {
                    setBusy("reject");
                    await onReject();
                  } finally {
                    setBusy(null);
                  }
                }}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
              >
                {busy === "reject" ? "Rejecting..." : "Reject"}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
