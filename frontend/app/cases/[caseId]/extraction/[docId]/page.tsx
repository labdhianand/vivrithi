"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { getDocument, listExtractions, listPages, rerunExtraction, updateExtraction } from "@/lib/api";
import { toSelectedExtractionField } from "@/lib/extraction-highlight";
import type { DocumentRecord, ExtractionRecord, PageRecord, SelectedExtractionField } from "@/lib/types";
import { ExtractedDataTable } from "@/components/extraction/extracted-data-table";
import { PdfViewer } from "@/components/extraction/pdf-viewer";
import { Button } from "@/components/ui/button";

export default function DocumentExtractionPage({ params }: { params: { caseId: string; docId: string } }) {
  const searchParams = useSearchParams();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [pages, setPages] = useState<PageRecord[]>([]);
  const [extractions, setExtractions] = useState<ExtractionRecord[]>([]);
  const [activePage, setActivePage] = useState<number | undefined>(undefined);
  const [selectedField, setSelectedField] = useState<SelectedExtractionField | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const [nextDocument, nextPages, nextExtractions] = await Promise.all([
      getDocument(params.docId),
      listPages(params.docId),
      listExtractions(params.docId),
    ]);
    setDocument(nextDocument);
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
      const extraction = extractions.find((item) => item.id === extractionId);
      if (extraction) {
        setSelectedField(toSelectedExtractionField(extraction));
      }
    }
    if (page) {
      const pageNumber = Number(page);
      if (!Number.isNaN(pageNumber) && pageNumber > 0) {
        setActivePage(pageNumber);
      }
    }
  }, [extractions, searchParams]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Document Extraction
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">
            {document?.original_filename || "Source Document"}
          </h2>
          <p className="mt-1 text-sm text-slate-dim">
            {document?.user_category || document?.auto_category || "Unclassified"} · {extractions.length} extracted fields
          </p>
        </div>
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
          document={document}
          pages={pages}
          activePage={activePage}
          extractions={extractions}
          selectedField={selectedField}
          onSelectExtraction={(extractionId) => {
            const extraction = extractions.find((item) => item.id === extractionId);
            const nextSelection = extraction ? toSelectedExtractionField(extraction) : null;
            if (!nextSelection) {
              return;
            }
            setSelectedField(nextSelection);
            setActivePage(nextSelection.page);
          }}
          onSelectPage={setActivePage}
        />
        <ExtractedDataTable
          extractions={extractions}
          selectedExtractionId={selectedField?.extractionId}
          onSelectField={(field) => {
            setSelectedField(field);
            setActivePage(field.page);
          }}
          onSave={async (extractionId, value) => {
            await updateExtraction(extractionId, { user_edited_value: value, user_verified: true });
            await refresh();
          }}
        />
      </div>
    </div>
  );
}
