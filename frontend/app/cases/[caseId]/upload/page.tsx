"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { deleteDocument, getDocument, listDocuments, uploadDocuments } from "@/lib/api";
import { getDocumentCategory } from "@/lib/document-category";
import type { DocumentRecord } from "@/lib/types";
import { Dropzone } from "@/components/upload/dropzone";

const SLOT_COUNT = 8;

type SlotState = "empty" | "uploading" | "classifying" | "complete" | "error";

type UploadSlot = {
  state: SlotState;
  file: File | null;
  doc: DocumentRecord | null;
  error: string | null;
};

function createEmptySlot(): UploadSlot {
  return { state: "empty", file: null, doc: null, error: null };
}

function createInitialSlots() {
  return Array.from({ length: SLOT_COUNT }, () => createEmptySlot());
}

function createPollTokens() {
  return Array.from({ length: SLOT_COUNT }, () => null as symbol | null);
}

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function isClassified(document: DocumentRecord) {
  return Boolean(getDocumentCategory(document));
}

function isFailed(document: DocumentRecord) {
  return document.status === "failed" || document.processing_status === "failed";
}

function resolveSlotState(document: DocumentRecord): SlotState {
  if (isFailed(document)) {
    return "error";
  }
  if (isClassified(document)) {
    return "complete";
  }
  return "classifying";
}

function shouldPollDocument(document: DocumentRecord) {
  return !isFailed(document) && (!isClassified(document) || document.extraction_status === "processing");
}

function buildSlotFromDocument(document: DocumentRecord | null): UploadSlot {
  if (!document) {
    return createEmptySlot();
  }

  return {
    state: resolveSlotState(document),
    file: null,
    doc: document,
    error: isFailed(document) ? document.failure_reason || "Upload or classification failed." : null,
  };
}

export default function UploadPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const [slots, setSlots] = useState<UploadSlot[]>(createInitialSlots);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [replacingSlot, setReplacingSlot] = useState<number | null>(null);
  const mountedRef = useRef(true);
  const pollTokensRef = useRef<Array<symbol | null>>(createPollTokens());

  function updateSlot(slotIndex: number, next: UploadSlot | ((current: UploadSlot) => UploadSlot)) {
    setSlots((current) =>
      current.map((slot, index) =>
        index !== slotIndex ? slot : typeof next === "function" ? next(slot) : next,
      ),
    );
  }

  function cancelPolling(slotIndex: number) {
    pollTokensRef.current[slotIndex] = null;
  }

  async function pollDocument(slotIndex: number, documentId: string, file: File | null) {
    const token = Symbol(documentId);
    pollTokensRef.current[slotIndex] = token;

    while (mountedRef.current && pollTokensRef.current[slotIndex] === token) {
      try {
        const refreshed = await getDocument(documentId);
        if (!mountedRef.current || pollTokensRef.current[slotIndex] !== token) {
          return;
        }

        updateSlot(slotIndex, {
          state: resolveSlotState(refreshed),
          file,
          doc: refreshed,
          error: isFailed(refreshed) ? refreshed.failure_reason || "Upload or classification failed." : null,
        });

        if (!shouldPollDocument(refreshed)) {
          return;
        }
      } catch {
        if (!mountedRef.current || pollTokensRef.current[slotIndex] !== token) {
          return;
        }
      }

      await wait(3000);
    }
  }

  async function loadSlots() {
    const documents = await listDocuments(params.caseId);
    if (!mountedRef.current) {
      return;
    }

    const nextSlots = createInitialSlots();
    const pendingPolls: Array<{ slotIndex: number; document: DocumentRecord }> = [];

    documents.slice(0, SLOT_COUNT).forEach((document, slotIndex) => {
      nextSlots[slotIndex] = buildSlotFromDocument(document);
      if (shouldPollDocument(document)) {
        pendingPolls.push({ slotIndex, document });
      }
    });

    setSlots(nextSlots);
    setPageError(null);
    setLoading(false);

    pendingPolls.forEach(({ slotIndex, document }) => {
      void pollDocument(slotIndex, document.id, null);
    });
  }

  async function handleRetry(slotIndex: number) {
    const documentId = slots[slotIndex]?.doc?.id;
    cancelPolling(slotIndex);

    if (documentId) {
      try {
        await deleteDocument(documentId);
      } catch {
        // Ignore delete failures and reset the slot locally.
      }
    }

    updateSlot(slotIndex, createEmptySlot());
  }

  async function handleFileSelect(slotIndex: number, file: File) {
    const currentSlot = slots[slotIndex];
    if (currentSlot.state === "uploading") {
      return;
    }

    setPageError(null);
    cancelPolling(slotIndex);
    updateSlot(slotIndex, {
      state: "uploading",
      file,
      doc: currentSlot.doc,
      error: null,
    });

    try {
      if (currentSlot.doc?.id) {
        try {
          await deleteDocument(currentSlot.doc.id);
        } catch {
          // Ignore replace delete failures and continue with the new upload.
        }
      }

      const uploaded = await uploadDocuments(params.caseId, [file]);
      const uploadedDocument = uploaded[0];
      if (!uploadedDocument) {
        throw new Error("Upload did not return a document.");
      }

      updateSlot(slotIndex, {
        state: resolveSlotState(uploadedDocument),
        file,
        doc: uploadedDocument,
        error: isFailed(uploadedDocument) ? uploadedDocument.failure_reason || "Upload failed." : null,
      });

      if (shouldPollDocument(uploadedDocument)) {
        void pollDocument(slotIndex, uploadedDocument.id, file);
      }
    } catch (err) {
      updateSlot(slotIndex, {
        state: "error",
        file,
        doc: currentSlot.doc,
        error: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  }

  async function handleReplace(slotIndex: number) {
    setPageError(null);
    setReplacingSlot(slotIndex);
    try {
      await handleRetry(slotIndex);
    } finally {
      if (mountedRef.current) {
        setReplacingSlot((current) => (current === slotIndex ? null : current));
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);

    void loadSlots().catch((err) => {
      if (!mountedRef.current) {
        return;
      }
      setPageError(err instanceof Error ? err.message : "Failed to load documents.");
      setLoading(false);
    });

    return () => {
      mountedRef.current = false;
      pollTokensRef.current = createPollTokens();
    };
  }, [params.caseId]);

  const readyCount = slots.filter((slot) => slot.state === "complete").length;

  return (
    <div className="rounded-[28px] bg-[#1a0a0f] p-4 sm:p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">Document intake</p>
              <h1 className="mt-2 text-3xl font-semibold text-[#fce4ec]">Upload Documents</h1>
              <p className="mt-2 max-w-3xl text-sm text-[#ad6883]">
                Drop any financial document into any slot. AI classification runs automatically after upload, and
                full-document extraction continues in the background.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-[#7a2550] bg-[#3d1a2a] px-4 py-2 text-sm font-medium text-[#f48fb1]">
                {readyCount} of 8 documents uploaded
              </span>
              <span className="rounded-full border border-[#4a1530] bg-[#16080d] px-4 py-2 text-sm text-[#ad6883]">
                Minimum 3 required
              </span>
            </div>
          </div>
        </div>

        {pageError ? (
          <div className="rounded-xl border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300">{pageError}</div>
        ) : null}

        {loading ? (
          <div className="flex min-h-[280px] items-center justify-center rounded-xl border border-[#4a1530] bg-[#1f0d16]">
            <div className="flex items-center gap-3 text-sm text-[#ad6883]">
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-[#e91e8c]/30 border-t-[#e91e8c]" />
              <span>Loading upload zones...</span>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {slots.map((slot, index) => (
              <Dropzone
                key={`slot-${index + 1}`}
                label={`Document ${index + 1}`}
                state={slot.state}
                error={slot.error}
                document={slot.doc}
                file={slot.file}
                replacing={replacingSlot === index}
                onFileSelect={(file) => {
                  void handleFileSelect(index, file);
                }}
                onReplace={() => {
                  void handleReplace(index);
                }}
                onRetry={() => {
                  void handleRetry(index);
                }}
              />
            ))}
          </div>
        )}

        <div className="flex flex-col gap-4 rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-[#ad6883]">Ready to continue</p>
            <h2 className="mt-2 text-xl font-semibold text-[#fce4ec]">{readyCount} of 8 documents uploaded</h2>
            <p className="mt-1 text-sm text-[#ad6883]">
              Continue once at least 3 documents have been uploaded and classified.
            </p>
          </div>

          <button
            type="button"
            disabled={readyCount < 3}
            onClick={() => router.push(`/cases/${params.caseId}/classify`)}
            className="min-w-[240px] rounded-xl bg-[#e91e8c] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#c4187a] disabled:cursor-not-allowed disabled:bg-[#7a2550] disabled:text-[#f0b7cf]"
          >
            Continue to Classification
          </button>
        </div>
      </div>
    </div>
  );
}
