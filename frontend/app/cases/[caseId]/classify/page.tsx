"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { approveClassification, listDocuments, rejectClassification } from "@/lib/api";
import { getDocumentExtractionStatus } from "@/lib/document-category";
import type { DocumentRecord } from "@/lib/types";
import { ClassificationCard } from "@/components/classification/classification-card";

const ACTIVE_EXTRACTION_STATUSES = new Set(["processing"]);

export default function ClassificationPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const nextDocuments = await listDocuments(params.caseId);
    setDocuments(nextDocuments);
    return nextDocuments;
  };

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : "Failed to load documents"));
  }, [params.caseId]);

  useEffect(() => {
    if (!processing) {
      return;
    }
    const intervalId = window.setInterval(() => {
      refresh().catch(() => {});
    }, 3000);
    return () => window.clearInterval(intervalId);
  }, [processing, params.caseId]);

  useEffect(() => {
    if (documents.length === 0) {
      return;
    }
    setProcessing(documents.some((document) => ACTIVE_EXTRACTION_STATUSES.has(getDocumentExtractionStatus(document) || "")));
  }, [documents, params.caseId]);

  const reviewedCount = useMemo(
    () => documents.filter((document) => ["approved", "user_approved", "rejected"].includes(document.classification_status)).length,
    [documents],
  );
  const allReviewed = documents.length > 0 && reviewedCount === documents.length;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 text-[#fce4ec]">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#fce4ec]">Classification Review</h1>
          <p className="mt-1 text-[#ad6883]">Approve or reject each uploaded document before moving to schema setup.</p>
        </div>
        <div className="rounded-full border border-[#4a1530] bg-[#1f0d16] px-4 py-2 text-sm font-medium text-[#f48fb1]">
          {reviewedCount}/{documents.length} reviewed
        </div>
      </div>

      {processing ? (
        <div className="mb-6 rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-4 py-3 text-sm text-[#ff6bb5]">
          Full-document extraction is still running in the background. Classification is already available and cards will keep updating automatically.
        </div>
      ) : null}

      {error ? (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      ) : null}

      <div className="space-y-4">
        {documents.map((document) => (
          <ClassificationCard
            key={document.id}
            document={document}
            onApprove={async (category) => {
              await approveClassification(document.id, category);
              await refresh();
            }}
            onReject={async () => {
              await rejectClassification(document.id);
              await refresh();
            }}
          />
        ))}
      </div>

      {documents.length === 0 ? (
        <div className="mt-6 rounded-xl border border-[#4a1530] bg-[#1f0d16] p-8 text-center text-[#ad6883] shadow-card">
          No documents uploaded yet.
        </div>
      ) : null}

      {allReviewed ? (
        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={() => router.push(`/cases/${params.caseId}/schema`)}
            className="rounded-lg bg-[#e91e8c] px-4 py-2 font-medium text-white transition-colors hover:bg-[#c4187a]"
          >
            Proceed to Schema
          </button>
        </div>
      ) : null}
    </div>
  );
}
