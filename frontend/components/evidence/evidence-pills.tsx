"use client";

import Link from "next/link";

import type { EvidenceRef } from "@/lib/types";

function labelForRef(ref: EvidenceRef) {
  const label = ref.label || "Source";
  if (ref.kind === "extraction") {
    const page = ref.page_number ? ` p.${ref.page_number}` : "";
    return `${label}${page}`;
  }
  return label;
}

function hrefForRef(ref: EvidenceRef, caseId?: string) {
  if (ref.kind === "extraction" && caseId && ref.document_id) {
    const params = new URLSearchParams();
    if (ref.extraction_id) {
      params.set("extractionId", ref.extraction_id);
    }
    if (ref.page_number) {
      params.set("page", String(ref.page_number));
    }
    const query = params.toString();
    return `/cases/${caseId}/extraction/${ref.document_id}${query ? `?${query}` : ""}`;
  }
  if (ref.kind === "research" && ref.url) {
    return ref.url;
  }
  return null;
}

export function EvidencePills({
  refs,
  caseId,
}: {
  refs?: EvidenceRef[] | null;
  caseId?: string;
}) {
  const items = (refs || []).filter(Boolean);
  if (!items.length) {
    return null;
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {items.map((ref, index) => {
        const href = hrefForRef(ref, caseId);
        const label = labelForRef(ref);
        const key = `${ref.kind}-${ref.extraction_id || ref.research_id || ref.note_id || index}`;
        const className =
          "inline-flex items-center rounded-full border border-white/[0.08] bg-surface-300/60 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-dim transition-colors hover:border-white/[0.14] hover:text-slate-bright";

        if (!href) {
          return (
            <span key={key} className={className}>
              {label}
            </span>
          );
        }

        if (ref.kind === "research") {
          return (
            <a key={key} href={href} target="_blank" rel="noreferrer" className={className}>
              {label}
            </a>
          );
        }

        return (
          <Link key={key} href={href} className={className}>
            {label}
          </Link>
        );
      })}
    </div>
  );
}
