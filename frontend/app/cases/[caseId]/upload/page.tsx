"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  deleteDocument,
  getDocument,
  listDocuments,
  updateDocumentClassification,
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
  const category = document.user_category || document.auto_category;
  if (!category) {
    return null;
  }

  return CATEGORY_TO_SECTION_KEY[category] || null;
}

function latestDocumentForSection(sectionKey: SectionKey, documents: DocumentRecord[]) {
  return documents
    .filter((document) => getSectionKey(document) === sectionKey)
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0] || null;
}

function isClassificationReady(document: DocumentRecord) {
  if (document.auto_category) {
    return true;
  }

  return ["auto_classified", "approved", "user_approved", "rejected"].includes(document.classification_status);
}

function buildSectionFromDocument(document: DocumentRecord | null): SectionRecord {
  if (!document) {
    return createEmptySection();
  }

  if (document.processing_status === "failed") {
    return {
      state: "error",
      file: null,
      doc: document,
      error: document.failure_reason || "Upload or classification failed.",
    };
  }

  if (isClassificationReady(document)) {
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
      [sectionKey]: typeof next === "function" ? (next as (current: SectionRecord) => SectionRecord)(current[sectionKey]) : next,
    }));
  }

  function cancelPolling(sectionKey: SectionKey) {
    pollTokensRef.current[sectionKey] = null;
  }

  async function pollUntilClassified(sectionKey: SectionKey, documentId: string, file: File | null) {
    const token = Symbol(documentId);
    pollTokensRef.current[sectionKey] = token;

    while (mountedRef.current && pollTokensRef.current[sectionKey] === token) {
      try {
        const nextDocument = await getDocument(documentId);
        if (!mountedRef.current || pollTokensRef.current[sectionKey] !== token) {
          return;
        }

        if (nextDocument.processing_status === "failed") {
          updateSection(sectionKey, {
            state: "error",
            file,
            doc: nextDocument,
            error: nextDocument.failure_reason || "Upload or classification failed.",
          });
          return;
        }

        if (isClassificationReady(nextDocument)) {
          updateSection(sectionKey, (current) => ({
            state: "complete",
            file: current.file || file,
            doc: nextDocument,
            error: null,
          }));
          return;
        }

        updateSection(sectionKey, (current) => ({
          state: "classifying",
          file: current.file || file,
          doc: nextDocument,
          error: null,
        }));
      } catch (err) {
        if (!mountedRef.current || pollTokensRef.current[sectionKey] !== token) {
          return;
        }

        updateSection(sectionKey, (current) => ({
          state: "error",
          file: current.file || file,
          doc: current.doc,
          error: err instanceof Error ? err.message : "Failed to check document classification.",
        }));
        return;
      }

      await wait(2000);
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

      if (matchedDocument && nextSections[section.key].state === "classifying") {
        pendingPolls.push({ sectionKey: section.key, document: matchedDocument });
      }
    }

    setSections(nextSections);
    setPageError(null);
    setLoading(false);

    pendingPolls.forEach(({ sectionKey, document }) => {
      void pollUntilClassified(sectionKey, document.id, null);
    });
  }

  async function handleFileSelect(sectionKey: SectionKey, file: File) {
    const sectionConfig = REQUIRED_UPLOADS.find((section) => section.key === sectionKey);
    const currentSection = sections[sectionKey];
    if (!sectionConfig || ["uploading", "classifying", "complete"].includes(currentSection.state)) {
      return;
    }

    setPageError(null);
    cancelPolling(sectionKey);

    let cleanupDocument: DocumentRecord | null = currentSection.doc;

    updateSection(sectionKey, {
      state: "uploading",
      file,
      doc: currentSection.doc,
      error: null,
    });

    try {
      if (currentSection.doc) {
        await deleteDocument(currentSection.doc.id);
        cleanupDocument = null;
      }

      const uploaded = await uploadDocuments(params.caseId, [file]);
      const uploadedDocument = uploaded[0];
      if (!uploadedDocument) {
        throw new Error("Upload did not return a document.");
      }

      cleanupDocument = uploadedDocument;

      const slottedDocument = await updateDocumentClassification(uploadedDocument.id, {
        user_category: sectionConfig.category,
        classification_status: "pending",
      });

      cleanupDocument = slottedDocument;

      updateSection(sectionKey, {
        state: "classifying",
        file,
        doc: slottedDocument,
        error: null,
      });

      void pollUntilClassified(sectionKey, slottedDocument.id, file);
    } catch (err) {
      updateSection(sectionKey, {
        state: "error",
        file,
        doc: cleanupDocument,
        error: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  }

  async function handleReplace(sectionKey: SectionKey) {
    const currentSection = sections[sectionKey];
    if (!currentSection.doc) {
      updateSection(sectionKey, createEmptySection());
      return;
    }

    setPageError(null);
    setReplacingSection(sectionKey);
    cancelPolling(sectionKey);

    try {
      await deleteDocument(currentSection.doc.id);
      updateSection(sectionKey, createEmptySection());
    } catch (err) {
      setPageError(err instanceof Error ? err.message : "Failed to remove the existing document.");
    } finally {
      if (mountedRef.current) {
        setReplacingSection((current) => (current === sectionKey ? null : current));
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);

    loadSections().catch((err) => {
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
                Each section accepts exactly one file. Uploads run independently, and a section stays locked until you explicitly replace its document.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Badge tone={readyCount >= 3 ? "success" : "info"}>{readyCount} of 5 ready</Badge>
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
                />
              </div>
            ))}
          </div>
        )}

        <Card className="animate-slide-up stagger-2 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Ready to review</p>
            <h2 className="mt-2 text-xl font-semibold text-slate-bright">{readyCount} of 5 documents ready</h2>
            <p className="mt-1 text-sm text-slate-dim">
              The classification step unlocks after at least 3 sections reach the complete state.
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
