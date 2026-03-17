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
  tone = "dark",
}: {
  refs?: EvidenceRef[] | null;
  caseId?: string;
  tone?: "dark" | "light";
}) {
  const items = (refs || []).filter(Boolean);
  if (!items.length) {
    return null;
  }

  const className =
    tone === "light"
      ? "inline-flex items-center rounded-full border border-[#7a2550] bg-[#3d1a2a] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#ff6bb5] transition-colors hover:border-[#e91e8c] hover:text-[#fce4ec]"
      : "inline-flex items-center rounded-full border border-[#4a1530] bg-[#2d1420] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#f48fb1] transition-colors hover:border-[#7a2550] hover:text-[#fce4ec]";

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {items.map((ref, index) => {
        const href = hrefForRef(ref, caseId);
        const label = labelForRef(ref);
        const key = `${ref.kind}-${ref.extraction_id || ref.research_id || ref.note_id || index}`;

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
