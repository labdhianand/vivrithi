"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listDocuments } from "@/lib/api";
import type { DocumentRecord } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function ExtractionOverviewPage({ params }: { params: { caseId: string } }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);

  useEffect(() => {
    listDocuments(params.caseId).then(setDocuments);
  }, [params.caseId]);

  return (
    <div className="space-y-2 text-[#fce4ec]">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Extraction</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">Document Extractions</h2>
        </div>
        <Badge tone="neutral">{documents.length} documents</Badge>
      </div>

      <div className="grid gap-4">
        {documents.map((document) => (
          <Card key={document.id} className="border-[#4a1530] bg-[#1f0d16]">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">{document.user_category || document.auto_category || "Pending"}</p>
                <h3 className="mt-1.5 truncate text-base font-semibold text-slate-bright">{document.original_filename}</h3>
                <div className="mt-2 flex items-center gap-2">
                  <Badge
                    tone={
                      document.extraction_status === "extracted" || document.processing_status === "completed"
                        ? "success"
                        : document.extraction_status === "extraction_failed"
                          ? "warn"
                          : "warn"
                    }
                    pulse={document.extraction_status === "processing" || document.processing_status === "processing"}
                  >
                    {document.extraction_status || document.processing_status}
                  </Badge>
                </div>
              </div>
              <Link href={`/cases/${params.caseId}/extraction/${document.id}`}>
                <Button variant="secondary" size="sm">
                  Review extraction
                </Button>
              </Link>
            </div>
          </Card>
        ))}

        {documents.length === 0 && (
          <div className="panel p-10 text-center">
            <p className="text-sm text-slate-dim">No documents uploaded yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
