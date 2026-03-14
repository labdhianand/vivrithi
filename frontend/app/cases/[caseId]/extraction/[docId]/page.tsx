"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { listExtractions, listPages, rerunExtraction, updateExtraction } from "@/lib/api";
import type { ExtractionRecord, PageRecord } from "@/lib/types";
import { ExtractedDataTable } from "@/components/extraction/extracted-data-table";
import { PdfViewer } from "@/components/extraction/pdf-viewer";
import { Button } from "@/components/ui/button";

export default function DocumentExtractionPage({ params }: { params: { caseId: string; docId: string } }) {
  const searchParams = useSearchParams();
  const [pages, setPages] = useState<PageRecord[]>([]);
  const [extractions, setExtractions] = useState<ExtractionRecord[]>([]);
  const [activePage, setActivePage] = useState<number | undefined>(undefined);
  const [activeExtractionId, setActiveExtractionId] = useState<string | undefined>(undefined);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const [nextPages, nextExtractions] = await Promise.all([listPages(params.docId), listExtractions(params.docId)]);
    setPages(nextPages);
    setExtractions(nextExtractions);
    setActivePage((current) => current || nextPages[0]?.page_number);
  };

  useEffect(() => {
    refresh();
  }, [params.docId]);

  useEffect(() => {
    const extractionId = searchParams.get("extractionId");
    const page = searchParams.get("page");
    if (extractionId) {
      setActiveExtractionId(extractionId);
    }
    if (page) {
      const pageNumber = Number(page);
      if (!Number.isNaN(pageNumber) && pageNumber > 0) {
        setActivePage(pageNumber);
      }
    }
  }, [searchParams]);

  useEffect(() => {
    const current = extractions.find((item) => item.id === activeExtractionId);
    if (current?.source_page_number) {
      setActivePage(current.source_page_number);
    }
  }, [activeExtractionId, extractions]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
          Document Extraction
        </p>
        <Button
          variant="gold"
          size="sm"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            await rerunExtraction(params.docId);
            await refresh();
            setBusy(false);
          }}
        >
          {busy ? "Re-extracting\u2026" : "Re-run extraction"}
        </Button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <PdfViewer
          documentId={params.docId}
          pages={pages}
          activePage={activePage}
          extractions={extractions}
          activeExtractionId={activeExtractionId}
          onSelectExtraction={setActiveExtractionId}
          onSelectPage={setActivePage}
        />
        <ExtractedDataTable
          extractions={extractions}
          activeExtractionId={activeExtractionId}
          onHighlight={setActiveExtractionId}
          onSave={async (extractionId, value) => {
            await updateExtraction(extractionId, { user_edited_value: value, user_verified: true });
            await refresh();
          }}
        />
      </div>
    </div>
  );
}
