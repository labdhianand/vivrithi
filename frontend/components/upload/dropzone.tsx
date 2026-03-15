"use client";

import { useRef, useState } from "react";

import type { DocumentRecord } from "@/lib/types";

type DropzoneState = "idle" | "uploading" | "success" | "error";

function formatBytes(bytes: number | null | undefined) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function Dropzone({
  title,
  description,
  state,
  error,
  document,
  onFileSelect,
}: {
  title: string;
  description: string;
  state: DropzoneState;
  error?: string;
  document?: DocumentRecord | null;
  onFileSelect: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const borderClass =
    state === "success"
      ? "border-2 border-emerald-500"
      : state === "error"
        ? "border border-red-400"
        : state === "uploading"
          ? "border border-blue-400"
          : "border border-dashed border-slate-300";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-slate-900">{title}</h3>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        {state === "success" ? (
          <div className="rounded-full bg-emerald-100 p-2 text-emerald-600">
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 10.5 8.5 14 15 6.5" />
            </svg>
          </div>
        ) : null}
      </div>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
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
          const nextFile = Array.from(event.dataTransfer.files)[0];
          if (nextFile) {
            onFileSelect(nextFile);
          }
        }}
        className={`mt-4 flex w-full flex-col items-center justify-center rounded-xl px-4 py-8 text-center transition-colors ${borderClass} ${dragActive ? "bg-blue-50" : "bg-slate-50"}`}
      >
        {state === "uploading" ? (
          <>
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600" />
            <p className="mt-3 font-medium text-slate-900">Uploading...</p>
          </>
        ) : state === "success" && document ? (
          <>
            <p className="max-w-full truncate font-medium text-slate-900">{document.original_filename}</p>
            <p className="mt-1 text-sm text-slate-500">{formatBytes(document.file_size_bytes)}</p>
            <div className="mt-3 inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700">
              {(document.user_category || document.auto_category || "Pending").replace(/_/g, " ")}
              {document.auto_category_confidence ? ` - ${Math.round(Number(document.auto_category_confidence) * 100)}%` : ""}
            </div>
          </>
        ) : state === "error" ? (
          <>
            <p className="font-medium text-red-600">{error || "Upload failed"}</p>
            <p className="mt-2 text-sm text-slate-500">Try again</p>
          </>
        ) : (
          <>
            <p className="font-medium text-slate-900">Drag & drop or click to browse</p>
            <p className="mt-2 text-sm text-slate-500">Accepts .pdf .xlsx .xls .png .jpg .jpeg</p>
          </>
        )}
      </button>

      <input
        ref={inputRef}
        type="file"
        hidden
        accept=".pdf,.xlsx,.xls,.png,.jpg,.jpeg"
        onChange={(event) => {
          const nextFile = Array.from(event.target.files || [])[0];
          if (nextFile) {
            onFileSelect(nextFile);
          }
        }}
      />

      {state === "error" ? (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}
