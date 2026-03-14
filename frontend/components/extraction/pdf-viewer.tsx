"use client";

import type { ExtractionRecord, PageRecord } from "@/lib/types";
import { getPageImageUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

import { BBoxOverlay } from "@/components/extraction/bbox-overlay";
import { Card } from "@/components/ui/card";

function toNumber(value?: string | null) {
  return value ? Number(value) : 0;
}

export function PdfViewer({
  documentId,
  pages,
  activePage,
  extractions,
  activeExtractionId,
  onSelectExtraction,
  onSelectPage,
}: {
  documentId: string;
  pages: PageRecord[];
  activePage?: number;
  extractions: ExtractionRecord[];
  activeExtractionId?: string;
  onSelectExtraction?: (id: string) => void;
  onSelectPage?: (pageNumber: number) => void;
}) {
  const page = pages.find((entry) => entry.page_number === activePage) || pages[0];
  const pageExtractions = extractions
    .filter((entry) => entry.source_page_number === page?.page_number && entry.bbox_x1)
    .map((entry) => ({
      id: entry.id,
      x1: toNumber(entry.bbox_x1),
      y1: toNumber(entry.bbox_y1),
      x2: toNumber(entry.bbox_x2),
      y2: toNumber(entry.bbox_y2),
    }));

  if (!page) {
    return (
      <Card>
        <p className="text-sm text-slate-dim">No parsed pages available yet.</p>
      </Card>
    );
  }

  return (
    <Card className="space-y-4">
      {/* Page selector pills */}
      <div className="flex flex-wrap gap-2">
        {pages.map((entry) => {
          const isActive = entry.page_number === page.page_number;
          return (
            <button
              key={entry.id}
              className={cn(
                "rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200",
                isActive
                  ? "bg-accent text-surface shadow-glow"
                  : "border border-white/[0.06] bg-surface-200 text-slate hover:border-white/[0.12] hover:text-slate-bright",
              )}
              onClick={() => onSelectPage?.(entry.page_number)}
            >
              Page {entry.page_number}
            </button>
          );
        })}
      </div>

      {/* Page image with dark border */}
      <div className="relative overflow-hidden rounded-xl border-2 border-white/[0.06] bg-surface-100">
        {page.page_image_path ? (
          <>
            <img
              alt={`Page ${page.page_number}`}
              className="w-full object-contain"
              src={getPageImageUrl(documentId, page.page_number)}
            />
            <BBoxOverlay boxes={pageExtractions} activeId={activeExtractionId} onSelect={onSelectExtraction} />
          </>
        ) : (
          <div className="max-h-[70vh] overflow-auto p-5">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Structured Preview
            </p>
            <pre className="whitespace-pre-wrap text-xs leading-6 text-slate">
              {page.raw_markdown || page.raw_text || "No renderable preview available for this page."}
            </pre>
          </div>
        )}
      </div>

      {/* Page count label */}
      <p className="text-center text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
        Page {page.page_number} of {pages.length}
      </p>
    </Card>
  );
}
