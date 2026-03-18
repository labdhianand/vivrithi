import type { DocumentRecord } from "@/lib/types";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

function statusTone(status: string): "default" | "success" | "warn" | "danger" | "info" | "neutral" {
  switch (status) {
    case "extracted":
    case "completed":
      return "success";
    case "processing":
    case "extracting":
      return "info";
    case "extraction_failed":
      return "warn";
    case "failed":
      return "danger";
    case "classified":
      return "warn";
    default:
      return "neutral";
  }
}

function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadProgress({ documents }: { documents: DocumentRecord[] }) {
  const completedCount = documents.filter(
    (d) => d.extraction_status === "extracted" || d.processing_status === "completed",
  ).length;

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Upload Progress
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-bright">
            Uploaded documents
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {completedCount > 0 && (
            <Badge tone="success">{completedCount} ready</Badge>
          )}
          <Badge tone="neutral">{documents.length} files</Badge>
        </div>
      </div>

      {/* Progress bar */}
      {documents.length > 0 && (
        <div className="mt-4">
          <div className="h-1 overflow-hidden rounded-full bg-surface-200">
            <div
              className="h-full rounded-full bg-gradient-to-r from-accent to-accent-glow transition-all duration-500"
              style={{ width: `${(completedCount / documents.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      <div className="mt-4 space-y-2">
        {documents.map((document, index) => (
          <div
            key={document.id}
            className={`animate-slide-up stagger-${Math.min(index + 1, 6)} flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/[0.06] bg-surface-200/60 px-4 py-3 transition-colors duration-200 hover:bg-surface-200`}
          >
            <div className="flex items-center gap-3">
              {/* File icon */}
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/10">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-accent">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-slate-bright">
                  {document.original_filename}
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-dim">
                  <span>{document.auto_category || document.user_category || "Pending classification"}</span>
                  {document.file_size_bytes && (
                    <>
                      <span className="text-white/10">|</span>
                      <span>{formatBytes(document.file_size_bytes)}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <Badge
              tone={statusTone(document.extraction_status || document.processing_status)}
              pulse={document.extraction_status === "processing" || document.processing_status === "processing"}
            >
              {document.extraction_status || document.processing_status}
            </Badge>
          </div>
        ))}

        {documents.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-sm text-slate-dim">No documents uploaded yet.</p>
          </div>
        )}
      </div>
    </Card>
  );
}
