"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { listDocuments, uploadDocuments } from "@/lib/api";
import type { DocumentRecord } from "@/lib/types";
import { Dropzone } from "@/components/upload/dropzone";

const REQUIRED_UPLOADS = [
  { key: "ALM", label: "ALM Report", description: "Liquidity buckets, maturity gaps, and liquidity coverage disclosures." },
  { key: "Shareholding_Pattern", label: "Shareholding Pattern", description: "Promoter ownership, pledge levels, and institutional holdings." },
  { key: "Borrowing_Profile", label: "Borrowing Profile", description: "Debt facilities, lender mix, maturities, and external ratings." },
  { key: "Annual_Report", label: "Annual Report", description: "Audited financials, auditor commentary, and governance disclosures." },
  { key: "Portfolio_Performance", label: "Portfolio Performance", description: "AUM, NPA, collections, capital adequacy, and yield trends." },
] as const;

type ZoneStatus = "idle" | "uploading" | "success" | "error";

function latestMatch(category: string, documents: DocumentRecord[]) {
  return documents
    .filter((document) => (document.user_category || document.auto_category) === category)
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0];
}

export default function UploadPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [zoneStates, setZoneStates] = useState<Record<string, { status: ZoneStatus; error?: string }>>({});
  const [zoneDocuments, setZoneDocuments] = useState<Record<string, DocumentRecord | null>>({});
  const [pageError, setPageError] = useState<string | null>(null);

  async function refresh() {
    const nextDocuments = await listDocuments(params.caseId);
    setDocuments(nextDocuments);
    setZoneDocuments(
      Object.fromEntries(REQUIRED_UPLOADS.map((zone) => [zone.key, latestMatch(zone.key, nextDocuments) || null])),
    );
    setZoneStates((current) => {
      const next = { ...current };
      for (const zone of REQUIRED_UPLOADS) {
        if (latestMatch(zone.key, nextDocuments)) {
          next[zone.key] = { status: "success" };
        } else if (!next[zone.key]) {
          next[zone.key] = { status: "idle" };
        }
      }
      return next;
    });
    return nextDocuments;
  }

  useEffect(() => {
    refresh().catch((err) => setPageError(err instanceof Error ? err.message : "Failed to load documents"));
  }, [params.caseId]);

  const uploadedCount = useMemo(
    () => REQUIRED_UPLOADS.filter((zone) => zoneDocuments[zone.key]).length,
    [zoneDocuments],
  );

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Upload Required Documents</h1>
        <p className="mt-1 text-slate-500">Upload the core appraisal pack. At least 3 of 5 documents are required to proceed.</p>
      </div>

      {pageError ? (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{pageError}</div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {REQUIRED_UPLOADS.map((zone) => (
          <Dropzone
            key={zone.key}
            title={zone.label}
            description={zone.description}
            state={zoneStates[zone.key]?.status || "idle"}
            error={zoneStates[zone.key]?.error}
            document={zoneDocuments[zone.key]}
            onFileSelect={async (file) => {
              try {
                setPageError(null);
                setZoneStates((current) => ({ ...current, [zone.key]: { status: "uploading" } }));
                const uploaded = await uploadDocuments(params.caseId, [file]);
                const directMatch =
                  uploaded.find((item) => item.original_filename === file.name) ||
                  uploaded.find((item) => (item.user_category || item.auto_category) === zone.key) ||
                  null;
                const refreshedDocuments = await refresh();
                setZoneDocuments((current) => ({
                  ...current,
                  [zone.key]: latestMatch(zone.key, refreshedDocuments) || directMatch,
                }));
                setZoneStates((current) => ({ ...current, [zone.key]: { status: "success" } }));
              } catch (err) {
                setZoneStates((current) => ({
                  ...current,
                  [zone.key]: {
                    status: "error",
                    error: err instanceof Error ? err.message : "Upload failed",
                  },
                }));
              }
            }}
          />
        ))}
      </div>

      <div className="mt-8 flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm font-medium text-slate-700">{uploadedCount} of 5 documents uploaded</p>
        <button
          type="button"
          disabled={uploadedCount < 3}
          onClick={() => router.push(`/cases/${params.caseId}/classify`)}
          className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
