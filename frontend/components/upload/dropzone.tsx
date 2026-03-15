"use client";

import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

export function Dropzone({
  files,
  onFilesChange,
}: {
  files: File[];
  onFilesChange: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const isSupported = (file: File) => {
    const name = file.name.toLowerCase();
    return (
      file.type === "application/pdf" ||
      file.type === "image/png" ||
      file.type === "image/jpeg" ||
      file.type === "image/tiff" ||
      name.endsWith(".pdf") ||
      name.endsWith(".xlsx") ||
      name.endsWith(".xls") ||
      name.endsWith(".csv") ||
      name.endsWith(".png") ||
      name.endsWith(".jpg") ||
      name.endsWith(".jpeg") ||
      name.endsWith(".tiff")
    );
  };

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setDragActive(false);
      const dropped = Array.from(event.dataTransfer.files).filter(isSupported);
      if (dropped.length > 0) {
        onFilesChange(dropped);
      }
    },
    [onFilesChange],
  );

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragActive(false);
  }, []);

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`
        group relative overflow-hidden rounded-2xl border-2 border-dashed
        transition-all duration-300
        ${
          dragActive
            ? "border-accent-glow bg-accent/[0.06] shadow-[0_0_40px_rgba(6,182,212,0.12)]"
            : "border-accent/30 bg-surface-100/60 hover:border-accent/50 hover:bg-surface-100/80"
        }
      `}
    >
      {/* Subtle grid overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(6,182,212,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.4) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Corner accent marks */}
      <div className="pointer-events-none absolute left-3 top-3 h-4 w-4 border-l-2 border-t-2 border-accent/40 transition-colors duration-300 group-hover:border-accent-glow/60" />
      <div className="pointer-events-none absolute right-3 top-3 h-4 w-4 border-r-2 border-t-2 border-accent/40 transition-colors duration-300 group-hover:border-accent-glow/60" />
      <div className="pointer-events-none absolute bottom-3 left-3 h-4 w-4 border-b-2 border-l-2 border-accent/40 transition-colors duration-300 group-hover:border-accent-glow/60" />
      <div className="pointer-events-none absolute bottom-3 right-3 h-4 w-4 border-b-2 border-r-2 border-accent/40 transition-colors duration-300 group-hover:border-accent-glow/60" />

      <div className="relative flex flex-col items-center gap-5 px-8 py-10 md:flex-row md:items-center md:justify-between md:py-8">
        <div className="text-center md:text-left">
          {/* Upload icon */}
          <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent-glow">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-slate-bright">
            {dragActive ? "Release to upload" : "Drop the source pack"}
          </h3>
          <p className="mt-2 max-w-md text-sm text-slate">
            Upload ALM, shareholding pattern, borrowing profile, annual report, and portfolio/performance files. PDFs and spreadsheets are supported.
          </p>
          <p className="mt-1.5 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            PDF, XLSX, XLS, CSV, PNG, JPG, TIFF
          </p>
        </div>
        <Button variant="secondary" onClick={() => inputRef.current?.click()}>
          Select files
        </Button>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg,.tiff,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv,image/png,image/jpeg,image/tiff"
        multiple
        hidden
        onChange={(event) => {
          const nextFiles = Array.from(event.target.files || []).filter(isSupported);
          onFilesChange(nextFiles);
        }}
      />

      {/* Selected files list */}
      {files.length > 0 && (
        <div className="border-t border-white/[0.06] px-6 pb-5 pt-4">
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Selected files ({files.length})
          </p>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={`${file.name}-${file.size}`}
                className={`animate-slide-up stagger-${Math.min(index + 1, 6)} flex items-center justify-between rounded-xl border border-white/[0.06] bg-surface-200/80 px-4 py-2.5`}
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent-glow">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <span className="text-sm text-slate-bright">{file.name}</span>
                </div>
                <span className="text-xs text-slate-dim">{Math.round(file.size / 1024)} KB</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
