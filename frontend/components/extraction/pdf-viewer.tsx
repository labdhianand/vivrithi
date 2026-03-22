"use client";

import { useEffect, useMemo, useState } from "react";

import type { DocumentRecord, ExtractionRecord, PageRecord, SelectedExtractionField } from "@/lib/types";
import { getPageImageUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

import { BBoxOverlay } from "@/components/extraction/bbox-overlay";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

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

function toPageBox(extraction: ExtractionRecord) {
  if (!extraction.bbox) {
    return null;
  }
  return {
    id: extraction.id,
    x: extraction.bbox.x,
    y: extraction.bbox.y,
    width: extraction.bbox.width,
    height: extraction.bbox.height,
  };
}

export function PdfViewer({
  documentId,
  document,
  pages,
  activePage,
  extractions,
  selectedField,
  onSelectExtraction,
  onSelectPage,
}: {
  documentId: string;
  document: DocumentRecord | null;
  pages: PageRecord[];
  activePage?: number;
  extractions: ExtractionRecord[];
  selectedField?: SelectedExtractionField | null;
  onSelectExtraction?: (id: string) => void;
  onSelectPage?: (pageNumber: number) => void;
}) {
  const page = pages.find((entry) => entry.page_number === activePage) || pages[0];
  const currentIndex = page ? pages.findIndex((entry) => entry.id === page.id) : -1;
  const [imageFailed, setImageFailed] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [pageInput, setPageInput] = useState(page?.page_number ? String(page.page_number) : "1");
  const [pulseSelected, setPulseSelected] = useState(false);

  useEffect(() => {
    setImageFailed(false);
    setImageLoaded(false);
    if (page?.page_number) {
      setPageInput(String(page.page_number));
    }
  }, [documentId, page?.page_number]);

  useEffect(() => {
    if (!selectedField?.page || selectedField.page === page?.page_number) {
      return;
    }
    onSelectPage?.(selectedField.page);
  }, [onSelectPage, page?.page_number, selectedField?.page]);

  useEffect(() => {
    if (!selectedField?.fieldName) {
      setPulseSelected(false);
      return;
    }
    setPulseSelected(true);
    const timeoutId = window.setTimeout(() => {
      setPulseSelected(false);
    }, 2000);
    return () => window.clearTimeout(timeoutId);
  }, [
    selectedField?.bbox?.height,
    selectedField?.bbox?.width,
    selectedField?.bbox?.x,
    selectedField?.bbox?.y,
    selectedField?.extractionId,
    selectedField?.fieldName,
    selectedField?.page,
  ]);

  const isPdf = Boolean(
    document?.mime_type === "application/pdf"
      || document?.original_filename?.toLowerCase().endsWith(".pdf"),
  );

  const pageExtractions = extractions
    .filter((entry) => (entry.bbox?.page || entry.source_page_number) === page?.page_number)
    .map(toPageBox)
    .filter((entry): entry is NonNullable<ReturnType<typeof toPageBox>> => Boolean(entry));

  const selectedBox =
    selectedField?.page === page?.page_number && selectedField.bbox
      ? {
          id: selectedField.extractionId || `selected-${selectedField.fieldName}`,
          x: selectedField.bbox.x,
          y: selectedField.bbox.y,
          width: selectedField.bbox.width,
          height: selectedField.bbox.height,
        }
      : null;

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
                <p className="text-sm text-slate-dim">Rendering page preview...</p>
              </div>
            )}
            <img
              alt={`Page ${page.page_number}`}
              className="block h-auto w-full"
              src={imageUrl}
              onError={() => setImageFailed(true)}
              onLoad={() => setImageLoaded(true)}
            />
            {imageLoaded ? (
              <BBoxOverlay
                boxes={pageExtractions}
                selectedBoxId={selectedField?.page === page.page_number ? selectedField.extractionId : undefined}
                selectedBox={selectedBox}
                pulseSelected={pulseSelected}
                onSelect={onSelectExtraction}
              />
            ) : null}
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
        <span>
          {selectedField?.page === page.page_number && !selectedField.bbox
            ? "Selected field has page metadata only. No bounding box was returned for highlight."
            : canRenderImage
              ? "Click a field row to jump to its bounding box on the rendered page."
              : "Image preview unavailable for this document type."}
        </span>
        <span>{page.parser_used || "parser unknown"}</span>
      </div>
    </Card>
  );
}
