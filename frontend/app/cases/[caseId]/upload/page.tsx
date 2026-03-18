"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  deleteDocument,
  getDocument,
  getDocumentExtractionStatus,
  listDocuments,
  uploadDocuments,
} from "@/lib/api";
import type { DocumentRecord } from "@/lib/types";
import { Dropzone } from "@/components/upload/dropzone";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const REQUIRED_UPLOADS = [
  {
    key: "alm",
    category: "ALM",
    label: "ALM Report",
    description: "Liquidity buckets, maturity gaps, and liquidity coverage disclosures.",
  },
  {
    key: "shareholding",
    category: "Shareholding_Pattern",
    label: "Shareholding Pattern",
    description: "Promoter ownership, pledge levels, and institutional holdings.",
  },
  {
    key: "borrowing",
    category: "Borrowing_Profile",
    label: "Borrowing Profile",
    description: "Debt facilities, lender mix, maturities, and external ratings.",
  },
  {
    key: "annual",
    category: "Annual_Report",
    label: "Annual Report",
    description: "Audited financials, auditor commentary, and governance disclosures.",
  },
  {
    key: "portfolio",
    category: "Portfolio_Performance",
    label: "Portfolio Performance",
    description: "AUM, NPA, collections, capital adequacy, and yield trends.",
  },
] as const;

type SectionKey = (typeof REQUIRED_UPLOADS)[number]["key"];
type SectionState = "empty" | "uploading" | "classifying" | "complete" | "error";
type SectionRecord = {
  state: SectionState;
  file: File | null;
  doc: DocumentRecord | null;
  error: string | null;
};
type SectionsState = Record<SectionKey, SectionRecord>;

const CATEGORY_TO_SECTION_KEY: Record<string, SectionKey> = {
  ALM: "alm",
  Shareholding_Pattern: "shareholding",
  Borrowing_Profile: "borrowing",
  Annual_Report: "annual",
  Portfolio_Performance: "portfolio",
};

function createEmptySection(): SectionRecord {
  return { state: "empty", file: null, doc: null, error: null };
}

function createInitialSections(): SectionsState {
  return {
    alm: createEmptySection(),
    shareholding: createEmptySection(),
    borrowing: createEmptySection(),
    annual: createEmptySection(),
    portfolio: createEmptySection(),
  };
}

function createPollMap(): Record<SectionKey, symbol | null> {
  return {
    alm: null,
    shareholding: null,
    borrowing: null,
    annual: null,
    portfolio: null,
  };
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function getSectionKey(document: DocumentRecord) {
  const category = document.user_category || document.auto_category || document.doc_type;
  if (!category) {
    return null;
  }
  return CATEGORY_TO_SECTION_KEY[category] || null;
}

function latestDocumentForSection(sectionKey: SectionKey, documents: DocumentRecord[]) {
  return (
    documents
      .filter((document) => getSectionKey(document) === sectionKey)
      .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0] || null
  );
}

function isClassified(document: DocumentRecord) {
  return document.status === "classified" || Boolean(document.auto_category || document.doc_type);
}

function isFailed(document: DocumentRecord) {
  return document.status === "failed" || document.processing_status === "failed";
}

function buildSectionFromDocument(document: DocumentRecord | null): SectionRecord {
  if (!document) {
    return createEmptySection();
  }
  if (isFailed(document)) {
    return {
      state: "error",
      file: null,
      doc: document,
      error: document.failure_reason || "Upload or classification failed.",
    };
  }
  if (isClassified(document)) {
    return {
      state: "complete",
      file: null,
      doc: document,
      error: null,
    };
  }
  return {
    state: "classifying",
    file: null,
    doc: document,
    error: null,
  };
}

export default function UploadPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const [sections, setSections] = useState<SectionsState>(createInitialSections);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [replacingSection, setReplacingSection] = useState<SectionKey | null>(null);
  const mountedRef = useRef(true);
  const pollTokensRef = useRef<Record<SectionKey, symbol | null>>(createPollMap());

  function updateSection(sectionKey: SectionKey, next: SectionRecord | ((current: SectionRecord) => SectionRecord)) {
    setSections((current) => ({
      ...current,
      [sectionKey]:
        typeof next === "function" ? (next as (current: SectionRecord) => SectionRecord)(current[sectionKey]) : next,
    }));
  }

  function cancelPolling(sectionKey: SectionKey) {
    pollTokensRef.current[sectionKey] = null;
  }

  async function pollExtractionStatus(sectionKey: SectionKey, documentId: string, file: File | null) {
    const token = Symbol(documentId);
    pollTokensRef.current[sectionKey] = token;

    while (mountedRef.current && pollTokensRef.current[sectionKey] === token) {
      try {
        const nextStatus = await getDocumentExtractionStatus(documentId);
        if (!mountedRef.current || pollTokensRef.current[sectionKey] !== token) {
          return;
        }

        updateSection(sectionKey, (current) => ({
          state: current.doc && isFailed(current.doc) ? "error" : "complete",
          file: current.file || file,
          doc: current.doc
            ? {
                ...current.doc,
                extraction_status: nextStatus.extraction_status,
                extracted: nextStatus.extracted,
                processing_status:
                  nextStatus.extraction_status === "processing"
                    ? "processing"
                    : nextStatus.extraction_status,
              }
            : current.doc,
          error: null,
        }));

        if (nextStatus.extraction_status !== "processing") {
          const refreshed = await getDocument(documentId);
          if (!mountedRef.current || pollTokensRef.current[sectionKey] !== token) {
            return;
          }
          updateSection(sectionKey, {
            state: isFailed(refreshed) ? "error" : "complete",
            file,
            doc: refreshed,
            error: isFailed(refreshed) ? refreshed.failure_reason || "Upload or classification failed." : null,
          });
          return;
        }
      } catch {
        if (!mountedRef.current || pollTokensRef.current[sectionKey] !== token) {
          return;
        }
      }

      await wait(3000);
    }
  }

  async function loadSections() {
    const documents = await listDocuments(params.caseId);
    if (!mountedRef.current) {
      return;
    }

    const nextSections = createInitialSections();
    const pendingPolls: Array<{ sectionKey: SectionKey; document: DocumentRecord }> = [];

    for (const section of REQUIRED_UPLOADS) {
      const matchedDocument = latestDocumentForSection(section.key, documents);
      nextSections[section.key] = buildSectionFromDocument(matchedDocument);

      if (matchedDocument?.extraction_status === "processing") {
        pendingPolls.push({ sectionKey: section.key, document: matchedDocument });
      }
    }

    setSections(nextSections);
    setPageError(null);
    setLoading(false);

    pendingPolls.forEach(({ sectionKey, document }) => {
      void pollExtractionStatus(sectionKey, document.id, null);
    });
  }

  async function handleRetry(sectionKey: SectionKey) {
    const oldDocId = sections[sectionKey].doc?.id;
    cancelPolling(sectionKey);
    if (oldDocId) {
      try {
        await deleteDocument(oldDocId);
      } catch {
        // Ignore delete failures and reset locally.
      }
    }
    updateSection(sectionKey, createEmptySection());
  }

  async function handleFileSelect(sectionKey: SectionKey, file: File) {
    const currentSection = sections[sectionKey];
    if (currentSection.state === "uploading") {
      return;
    }

    setPageError(null);
    cancelPolling(sectionKey);
    updateSection(sectionKey, {
      state: "uploading",
      file,
      doc: currentSection.doc,
      error: null,
    });

    try {
      if (currentSection.doc?.id) {
        try {
          await deleteDocument(currentSection.doc.id);
        } catch {
          // Ignore delete failures and continue with the fresh upload.
        }
      }

      const uploaded = await uploadDocuments(params.caseId, [file]);
      const uploadedDocument = uploaded[0];
      if (!uploadedDocument) {
        throw new Error("Upload did not return a document.");
      }

      updateSection(sectionKey, {
        state: "complete",
        file,
        doc: uploadedDocument,
        error: null,
      });

      if (uploadedDocument.extraction_status === "processing") {
        void pollExtractionStatus(sectionKey, uploadedDocument.id, file);
      }
    } catch (err) {
      updateSection(sectionKey, {
        state: "error",
        file,
        doc: currentSection.doc,
        error: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  }

  async function handleReplace(sectionKey: SectionKey) {
    setPageError(null);
    setReplacingSection(sectionKey);
    try {
      await handleRetry(sectionKey);
    } finally {
      if (mountedRef.current) {
        setReplacingSection((current) => (current === sectionKey ? null : current));
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);

    void loadSections().catch((err) => {
      if (!mountedRef.current) {
        return;
      }
      setPageError(err instanceof Error ? err.message : "Failed to load documents.");
      setLoading(false);
    });

    return () => {
      mountedRef.current = false;
      pollTokensRef.current = createPollMap();
    };
  }, [params.caseId]);

  const readyCount = REQUIRED_UPLOADS.filter((section) => sections[section.key].state === "complete").length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="space-y-6">
        <Card glow className="animate-slide-up">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Document intake</p>
              <h1 className="mt-2 font-serif text-3xl text-slate-bright">Upload Required Documents</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-dim">
                Each section accepts exactly one file. Upload and classification complete fast, and full-document extraction continues in the background.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Badge tone={readyCount >= 3 ? "success" : "info"}>{readyCount} of 5 classified</Badge>
              <Badge tone="neutral">Minimum 3 required</Badge>
            </div>
          </div>
        </Card>

        {pageError ? (
          <div className="rounded-2xl border border-rose/30 bg-rose/[0.12] px-4 py-3 text-sm text-rose-glow">
            {pageError}
          </div>
        ) : null}

        {loading ? (
          <Card className="animate-slide-up flex items-center justify-center gap-3 py-16">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
            <span className="text-sm text-slate-dim">Loading upload sections...</span>
          </Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {REQUIRED_UPLOADS.map((section, index) => (
              <div key={section.key} className={`animate-slide-up stagger-${Math.min(index + 1, 6)}`}>
                <Dropzone
                  title={section.label}
                  description={section.description}
                  state={sections[section.key].state}
                  error={sections[section.key].error}
                  document={sections[section.key].doc}
                  file={sections[section.key].file}
                  replacing={replacingSection === section.key}
                  onFileSelect={(file) => {
                    void handleFileSelect(section.key, file);
                  }}
                  onReplace={() => {
                    void handleReplace(section.key);
                  }}
                  onRetry={() => {
                    void handleRetry(section.key);
                  }}
                />
              </div>
            ))}
          </div>
        )}

        <Card className="animate-slide-up stagger-2 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Ready to review</p>
            <h2 className="mt-2 text-xl font-semibold text-slate-bright">{readyCount} of 5 documents classified</h2>
            <p className="mt-1 text-sm text-slate-dim">
              Once at least 3 documents are classified you can continue. Full-text extraction will keep running in the background.
            </p>
          </div>

          <Button
            type="button"
            disabled={readyCount < 3}
            onClick={() => router.push(`/cases/${params.caseId}/classify`)}
            className="min-w-[220px]"
          >
            Continue to Classify
          </Button>
        </Card>
      </div>
    </div>
  );
}
