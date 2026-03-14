"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { listDocuments, uploadDocuments } from "@/lib/api";
import type { DocumentRecord } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropzone } from "@/components/upload/dropzone";
import { UploadProgress } from "@/components/upload/upload-progress";

export default function UploadPage({ params }: { params: { caseId: string } }) {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => listDocuments(params.caseId).then(setDocuments).catch((err) => setError(err.message));

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="animate-fade-in flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Document Upload
          </p>
          <h2 className="mt-1 text-lg font-semibold text-slate-bright">
            Source Pack Upload
          </h2>
        </div>
        <Badge tone="neutral">{documents.length} uploaded</Badge>
      </div>

      {/* Dropzone */}
      <div className="animate-slide-up stagger-1">
        <Dropzone files={files} onFilesChange={setFiles} />
      </div>

      {/* Action bar */}
      <div className="animate-slide-up stagger-2 flex items-center gap-4">
        <Button
          disabled={busy || files.length === 0}
          onClick={async () => {
            try {
              setBusy(true);
              setError(null);
              await uploadDocuments(params.caseId, files);
              setFiles([]);
              await refresh();
              router.push(`/cases/${params.caseId}/classify`);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Upload failed");
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Uploading..." : "Upload documents"}
        </Button>
        {files.length > 0 && !busy && (
          <Button variant="ghost" onClick={() => setFiles([])}>
            Clear selection
          </Button>
        )}
        {error && (
          <span className="text-sm text-rose-glow">{error}</span>
        )}
      </div>

      {/* Upload progress */}
      {documents.length > 0 && (
        <div className="animate-slide-up stagger-3">
          <UploadProgress documents={documents} />
        </div>
      )}
    </div>
  );
}
