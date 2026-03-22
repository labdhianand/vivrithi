"use client";

import { useRef, useState } from "react";

import {
  getDocumentCategory,
  getDocumentConfidence,
  getDocumentCurrentStage,
  getDocumentExtractionStatus,
  getDocumentFileSize,
  getDocumentProcessingStatus,
} from "@/lib/document-category";
import type { DocumentRecord } from "@/lib/types";

type DropzoneState = "empty" | "uploading" | "classifying" | "complete" | "error";

function formatBytes(bytes: number | null | undefined) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatCategory(category: string | null | undefined) {
  if (!category) {
    return "Pending classification";
  }

  return category
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => (part.toUpperCase() === part ? part : `${part[0].toUpperCase()}${part.slice(1).toLowerCase()}`))
    .join(" ");
}

function formatConfidence(confidence: string | null | undefined) {
  if (!confidence) {
    return null;
  }

  const numericConfidence = Number(confidence);
  if (Number.isNaN(numericConfidence)) {
    return null;
  }

  return `${Math.round(numericConfidence * 100)}%`;
}

function stageLabel(document?: DocumentRecord | null) {
  switch (getDocumentCurrentStage(document) || getDocumentProcessingStatus(document)) {
    case "queued":
      return "Queued for processing";
    case "triaging":
      return "Reviewing document structure";
    case "parsing":
      return "Reading pages and extracting text";
    case "classifying":
      return "Classifying document";
    case "extracting":
      return "Preparing extraction";
    default:
      return "Extraction running in background";
  }
}

export function Dropzone({
  label,
  state,
  error,
  document,
  file,
  replacing,
  onFileSelect,
  onReplace,
  onRetry,
}: {
  label: string;
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

  const activeFileName = file?.name || document?.original_filename || label;
  const activeFileSize = file?.size ?? getDocumentFileSize(document);
  const activeCategory = getDocumentCategory(document);
  const confidenceLabel = formatConfidence(getDocumentConfidence(document));
  const showPicker = state === "empty" || state === "error";
  const extractionStatus = getDocumentExtractionStatus(document);

  function openPicker() {
    inputRef.current?.click();
  }

  function handleSelectedFile(nextFile?: File) {
    if (!nextFile) {
      return;
    }

    onFileSelect(nextFile);
  }

  const borderClass = dragActive
    ? "border-[#e91e8c]"
    : state === "complete"
      ? "border-emerald-500"
      : state === "uploading" || state === "classifying"
        ? "border-[#e91e8c]"
        : state === "error"
          ? "border-red-500"
          : "border-[#4a1530] border-dashed";

  return (
    <div className={`relative flex min-h-[260px] flex-col rounded-xl border-2 bg-[#1f0d16] p-6 transition-colors ${borderClass}`}>
      {state === "complete" ? (
        <span className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-300">
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 10.5 8.5 14 15 6.5" />
          </svg>
        </span>
      ) : null}

      {showPicker ? (
        <>
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
            className="flex flex-1 flex-col items-center justify-center text-center"
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" className="text-[#ad6883]">
              <path d="M7 17.5A4.5 4.5 0 1 1 8.6 8.8 5.5 5.5 0 0 1 19 11a4 4 0 0 1-.5 8H13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M12 20V11m0 0-3 3m3-3 3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="mt-4 text-sm text-[#ad6883]">{label}</span>
            <span className="mt-2 text-xs text-[#7a2550]">Drop any financial document</span>
          </button>

          {state === "error" ? (
            <div className="mt-4 text-left">
              <p className="truncate text-sm font-medium text-[#fce4ec]">{activeFileName}</p>
              {activeFileSize ? <p className="mt-1 text-xs text-[#ad6883]">{formatBytes(activeFileSize)}</p> : null}
              <p className="mt-3 text-sm text-red-400">{error || "Upload or classification failed."}</p>
              <button
                type="button"
                onClick={onRetry}
                className="mt-4 rounded-lg border border-red-500/50 px-3 py-2 text-sm font-medium text-red-300 transition-colors hover:bg-red-950/40"
              >
                Try again
              </button>
            </div>
          ) : null}
        </>
      ) : null}

      {state === "uploading" ? (
        <div className="flex flex-1 flex-col justify-center">
          <p className="truncate pr-8 text-sm font-medium text-[#fce4ec]">{activeFileName}</p>
          {activeFileSize ? <p className="mt-1 text-xs text-[#ad6883]">{formatBytes(activeFileSize)}</p> : null}
          <div className="mt-4 flex items-center gap-3 text-[#f48fb1]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#ff6bb5]/30 border-t-[#ff6bb5]" />
            <span className="text-sm font-medium">Uploading...</span>
          </div>
        </div>
      ) : null}

      {state === "classifying" ? (
        <div className="flex flex-1 flex-col justify-center">
          <p className="truncate pr-8 text-sm font-medium text-[#fce4ec]">{activeFileName}</p>
          {activeFileSize ? <p className="mt-1 text-xs text-[#ad6883]">{formatBytes(activeFileSize)}</p> : null}
          <div className="mt-4 flex items-center gap-3 text-[#f48fb1]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#ff6bb5]/30 border-t-[#ff6bb5]" />
            <span className="text-sm font-medium">Classifying...</span>
          </div>
        </div>
      ) : null}

      {state === "complete" ? (
        <div className="flex flex-1 flex-col">
          <p className="truncate pr-8 text-sm font-medium text-[#fce4ec]">{activeFileName}</p>
          {activeFileSize ? <p className="mt-1 text-xs text-[#ad6883]">{formatBytes(activeFileSize)}</p> : null}

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="inline-flex rounded-full border border-[#7a2550] bg-[#3d1a2a] px-3 py-1 text-xs font-semibold text-[#ff6bb5]">
              {formatCategory(activeCategory)}
            </span>
            {confidenceLabel ? <span className="text-xs text-[#ad6883]">{confidenceLabel}</span> : null}
          </div>

          {extractionStatus === "processing" ? (
            <div className="mt-4 space-y-2">
              <div className="flex items-center gap-2 text-xs text-[#ad6883]">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#ad6883]/30 border-t-[#ad6883]" />
                <span>{stageLabel(document)}</span>
              </div>
              {(activeFileSize || 0) > 5_000_000 ? (
                <div className="rounded-lg border border-amber-900/70 bg-amber-950/40 px-3 py-2 text-xs text-amber-300">
                  Large document detected. Extraction is still running in the background.
                </div>
              ) : null}
            </div>
          ) : null}

          {extractionStatus === "extracted" ? (
            <div className="mt-4 flex items-center gap-2 text-xs text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span>Ready for schema</span>
            </div>
          ) : null}

          {extractionStatus === "extraction_failed" ? (
            <div className="mt-4 rounded-lg border border-amber-900/70 bg-amber-950/40 px-3 py-2 text-xs text-amber-300">
              Extraction completed partially. Some fields may need manual entry later.
            </div>
          ) : null}

          {onReplace ? (
            <button
              type="button"
              disabled={replacing}
              onClick={onReplace}
              className="mt-auto rounded-lg border border-[#7a2550] px-3 py-2 text-sm font-medium text-[#f48fb1] transition-colors hover:bg-[#3d1a2a] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {replacing ? "Removing..." : "Replace file"}
            </button>
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
