"use client";

import { useRef, useState } from "react";

import type { DocumentRecord } from "@/lib/types";
import { Button } from "@/components/ui/button";

type DropzoneState = "empty" | "uploading" | "classifying" | "complete" | "error";

function formatBytes(bytes: number | null | undefined) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatCategory(category: string | null | undefined) {
  if (!category) return "Pending classification";

  switch (category) {
    case "ALM":
      return "ALM Report";
    case "Shareholding_Pattern":
      return "Shareholding Pattern";
    case "Borrowing_Profile":
      return "Borrowing Profile";
    case "Annual_Report":
      return "Annual Report";
    case "Portfolio_Performance":
      return "Portfolio Performance";
    default:
      return category.replace(/_/g, " ");
  }
}

function formatConfidence(confidence: string | null | undefined) {
  if (!confidence) return null;
  return `${Math.round(Number(confidence) * 100)}% confident`;
}

function stageLabel(document?: DocumentRecord | null) {
  switch (document?.current_stage || document?.processing_status) {
    case "queued":
      return "Queued for processing";
    case "triaging":
      return "Reviewing document structure";
    case "parsing":
      return "Reading pages and extracting text";
    case "classifying":
      return "Classifying document...";
    case "extracting":
      return "Preparing extraction after classification";
    default:
      return "Classifying document...";
  }
}

export function Dropzone({
  title,
  description,
  state,
  error,
  document,
  file,
  replacing,
  onFileSelect,
  onReplace,
  onRetry,
}: {
  title: string;
  description: string;
  state: DropzoneState;
  error?: string | null;
  document?: DocumentRecord | null;
  file?: File | null;
  replacing?: boolean;
  onFileSelect: (file: File) => void;
  onReplace?: () => void;
  onRetry?: () => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const activeFileName = file?.name || document?.original_filename || "Untitled document";
  const activeFileSize = file?.size ?? document?.file_size_bytes;
  const confidenceLabel = formatConfidence(document?.auto_category_confidence);
  const showDropzone = state === "empty" || state === "error";

  function openPicker() {
    inputRef.current?.click();
  }

  function handleSelectedFile(nextFile?: File) {
    if (!nextFile) {
      return;
    }
    onFileSelect(nextFile);
  }

  return (
    <div className="panel border-gradient flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Required section</p>
          <h3 className="mt-2 text-lg font-semibold text-slate-bright">{title}</h3>
          <p className="mt-1 text-sm text-slate-dim">{description}</p>
        </div>
        {state === "complete" ? (
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald/15 text-emerald-glow">
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 10.5 8.5 14 15 6.5" />
            </svg>
          </span>
        ) : null}
      </div>

      {showDropzone ? (
        <div className="mt-5 flex flex-1 flex-col">
          {state === "error" ? (
            <div className="mb-3 rounded-2xl border border-rose/30 bg-rose/[0.12] px-4 py-3 text-sm text-rose-glow">
              {error || "Upload or classification failed. Try again."}
            </div>
          ) : null}

          <button
            type="button"
            onClick={openPicker}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setDragActive(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              handleSelectedFile(Array.from(event.dataTransfer.files)[0]);
            }}
            className={`flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed px-4 py-10 text-center transition-all duration-200 ${
              dragActive
                ? "border-accent/70 bg-accent/[0.12]"
                  : state === "error"
                  ? "border-rose/40 bg-rose/[0.06]"
                  : "border-[#4a1530] bg-[#2d1420]/40 hover:border-[#7a2550] hover:bg-[#2d1420]/70"
            }`}
          >
            <span className="text-sm font-semibold text-slate-bright">Drag &amp; drop or click to browse</span>
            <span className="mt-2 text-xs text-slate-dim">Accepts .pdf .xlsx .xls .png .jpg .jpeg</span>
          </button>

          {state === "error" ? (
            <div className="mt-3">
              <Button type="button" variant="secondary" size="sm" onClick={onRetry}>
                Try again
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}

      {state === "uploading" ? (
        <div className="mt-5 rounded-2xl border border-accent/25 bg-accent/[0.12] p-4">
          <p className="truncate text-sm font-semibold text-slate-bright">{activeFileName}</p>
          <div className="mt-4 flex items-center gap-3 text-sm text-[#f48fb1]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#ff6bb5]/30 border-t-[#ff6bb5]" />
            <span>Uploading...</span>
          </div>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[#2d1420]">
            <div className="h-full w-2/5 animate-pulse rounded-full bg-accent" />
          </div>
        </div>
      ) : null}

      {state === "classifying" ? (
        <div className="mt-5 rounded-2xl border border-[#7a2550]/50 bg-[#e91e8c]/10 p-4">
          <p className="truncate text-sm font-semibold text-slate-bright">{activeFileName}</p>
          <p className="mt-1 text-xs text-slate-dim">{formatBytes(activeFileSize)}</p>

          <div className="mt-4 flex items-center gap-3 text-sm text-[#f48fb1]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#ff6bb5]/30 border-t-[#ff6bb5]" />
            <span>Classifying document...</span>
          </div>

          <p className="mt-2 text-xs text-slate-dim">{stageLabel(document)}</p>

          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[#2d1420]">
            <div
              className="h-full rounded-full bg-[#ff6bb5] transition-all duration-500"
              style={{ width: `${Math.max(document?.progress_percent || 12, 12)}%` }}
            />
          </div>
        </div>
      ) : null}

      {state === "complete" ? (
        <div className="mt-5 rounded-2xl border border-emerald/25 bg-emerald/[0.08] p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-bright">{activeFileName}</p>
              <p className="mt-1 text-xs text-slate-dim">{formatBytes(activeFileSize)}</p>
            </div>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald/15 text-emerald-glow">
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 10.5 8.5 14 15 6.5" />
              </svg>
            </span>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center rounded-full bg-[#3d1a2a] px-3 py-1 text-xs font-semibold text-[#ff6bb5]">
              {formatCategory(document?.doc_type || document?.auto_category || document?.user_category)}
              {confidenceLabel ? ` - ${confidenceLabel}` : ""}
            </span>

            {onReplace ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={replacing}
                onClick={onReplace}
              >
                {replacing ? "Removing..." : "Replace file"}
              </Button>
            ) : null}
          </div>

          {document?.extraction_status === "processing" ? (
            <div className="mt-3 space-y-2">
              <div className="flex items-center gap-2 text-xs text-[#ad6883]">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#ad6883]/30 border-t-[#ad6883]" />
                <span>Extracting full document...</span>
              </div>
              {(activeFileSize || 0) > 5_000_000 ? (
                <div className="rounded-lg border border-amber-800 bg-amber-950 px-3 py-2 text-xs text-amber-300">
                  Large document detected - extracting in background. You can continue uploading other documents.
                </div>
              ) : null}
            </div>
          ) : null}

          {document?.extraction_status === "extracted" ? (
            <div className="mt-3 flex items-center gap-2 text-xs text-green-300">
              <span className="h-2 w-2 rounded-full bg-green-400" />
              <span>Ready for schema</span>
            </div>
          ) : null}

          {document?.extraction_status === "extraction_failed" ? (
            <div className="mt-3 rounded-lg border border-amber-800 bg-amber-950 px-3 py-2 text-xs text-amber-300">
              Extraction incomplete - some fields may need manual entry
            </div>
          ) : null}
        </div>
      ) : null}

      <input
        ref={inputRef}
        type="file"
        hidden
        accept=".pdf,.xlsx,.xls,.png,.jpg,.jpeg"
        onChange={(event) => {
          handleSelectedFile(Array.from(event.target.files || [])[0]);
          event.currentTarget.value = "";
        }}
      />
    </div>
  );
}
