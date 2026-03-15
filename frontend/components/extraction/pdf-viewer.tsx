"use client";

import { useEffect, useMemo, useState } from "react";

import type { DocumentRecord, ExtractionRecord, PageRecord } from "@/lib/types";
import { getPageImageUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

import { BBoxOverlay } from "@/components/extraction/bbox-overlay";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

function toNumber(value?: string | null) {
  return value ? Number(value) : 0;
}

function nearbyPages(pages: PageRecord[], activePage: number) {
  if (pages.length <= 9) {
    return pages;
  }
  const currentIndex = Math.max(0, pages.findIndex((entry) => entry.page_number === activePage));
  const start = Math.max(0, currentIndex - 2);
  const end = Math.min(pages.length, currentIndex + 3);
  const items = pages.slice(start, end);
  const first = pages[0];
  const last = pages[pages.length - 1];
  const result = [first, ...items, last];
  return result.filter((entry, index, array) => array.findIndex((candidate) => candidate.id === entry.id) === index);
}

export function PdfViewer({
  documentId,
  document,
  pages,
  activePage,
  extractions,
  activeExtractionId,
  onSelectExtraction,
  onSelectPage,
}: {
  documentId: string;
  document: DocumentRecord | null;
  pages: PageRecord[];
  activePage?: number;
  extractions: ExtractionRecord[];
  activeExtractionId?: string;
  onSelectExtraction?: (id: string) => void;
  onSelectPage?: (pageNumber: number) => void;
}) {
  const page = pages.find((entry) => entry.page_number === activePage) || pages[0];
  const currentIndex = page ? pages.findIndex((entry) => entry.id === page.id) : -1;
  const [imageFailed, setImageFailed] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [pageInput, setPageInput] = useState(page?.page_number ? String(page.page_number) : "1");

  useEffect(() => {
    setImageFailed(false);
    setImageLoaded(false);
    if (page?.page_number) {
      setPageInput(String(page.page_number));
    }
  }, [documentId, page?.page_number]);

  const isPdf = Boolean(
    document?.mime_type === "application/pdf"
      || document?.original_filename?.toLowerCase().endsWith(".pdf"),
  );

  const pageExtractions = extractions
    .filter((entry) => entry.source_page_number === page?.page_number && entry.bbox_x1)
    .map((entry) => ({
      id: entry.id,
      x1: toNumber(entry.bbox_x1),
      y1: toNumber(entry.bbox_y1),
      x2: toNumber(entry.bbox_x2),
      y2: toNumber(entry.bbox_y2),
    }));

  const visiblePages = useMemo(
    () => (page ? nearbyPages(pages, page.page_number) : pages.slice(0, 5)),
    [page, pages],
  );

  if (!page) {
    return (
      <Card>
        <p className="text-sm text-slate-dim">No parsed pages available yet.</p>
      </Card>
    );
  }

  const imageUrl = getPageImageUrl(documentId, page.page_number);
  const canRenderImage = isPdf && !imageFailed;

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Source Evidence
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">
            Page {page.page_number} of {pages.length}
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={pageExtractions.length > 0 ? "info" : "neutral"}>
            {pageExtractions.length} boxes
          </Badge>
          {page.has_tables && <Badge tone="warn">Table page</Badge>}
          <Badge tone="neutral">{page.content_type || "page"}</Badge>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/[0.06] bg-surface-200/50 p-3">
        <Button
          size="sm"
          variant="secondary"
          disabled={currentIndex <= 0}
          onClick={() => currentIndex > 0 && onSelectPage?.(pages[currentIndex - 1].page_number)}
        >
          Previous
        </Button>
        <Button
          size="sm"
          variant="secondary"
          disabled={currentIndex < 0 || currentIndex >= pages.length - 1}
          onClick={() => currentIndex >= 0 && currentIndex < pages.length - 1 && onSelectPage?.(pages[currentIndex + 1].page_number)}
        >
          Next
        </Button>
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-[0.2em] text-slate-dim">Jump</span>
          <Input
            className="w-20"
            inputMode="numeric"
            value={pageInput}
            onChange={(event) => setPageInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter") {
                return;
              }
              const pageNumber = Number(pageInput);
              if (!Number.isNaN(pageNumber) && pageNumber >= 1 && pageNumber <= pages.length) {
                onSelectPage?.(pageNumber);
              }
            }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {visiblePages.map((entry) => {
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

      <div className="relative min-h-[720px] overflow-hidden rounded-2xl border border-white/[0.06] bg-[#050816]">
        {canRenderImage ? (
          <>
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center bg-[#050816]">
                <p className="text-sm text-slate-dim">Rendering page preview…</p>
              </div>
            )}
            <img
              alt={`Page ${page.page_number}`}
              className="block h-auto w-full"
              src={imageUrl}
              onError={() => setImageFailed(true)}
              onLoad={() => setImageLoaded(true)}
            />
            {imageLoaded && (
              <BBoxOverlay
                boxes={pageExtractions}
                activeId={activeExtractionId}
                onSelect={onSelectExtraction}
              />
            )}
          </>
        ) : (
          <div className="max-h-[75vh] overflow-auto p-5">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Structured Preview
            </p>
            <pre className="whitespace-pre-wrap text-xs leading-6 text-slate">
              {page.raw_markdown || page.raw_text || "No renderable preview available for this page."}
            </pre>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-dim">
        <span>{canRenderImage ? "Bounding boxes are clickable on the rendered page." : "Image preview unavailable for this document type."}</span>
        <span>{page.parser_used || "parser unknown"}</span>
      </div>
    </Card>
  );
}
