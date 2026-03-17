"use client";

import { useEffect, useState } from "react";

import { createNote, deleteNote, listNotes } from "@/lib/api";
import type { AnalystNote } from "@/lib/types";
import { AnalystNoteForm } from "@/components/notes/analyst-note-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const sentimentTone = (s?: string | null) =>
  s === "positive" ? "success" : s === "negative" ? "danger" : "neutral";

const sentimentIcon = (s?: string | null) => {
  if (s === "positive")
    return (
      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
      </svg>
    );
  if (s === "negative")
    return (
      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6 9 12.75l4.286-4.286a11.948 11.948 0 0 1 5.814 5.518l2.74 1.22m0 0-5.94 2.281m5.94-2.28-2.28-5.941" />
      </svg>
    );
  return (
    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  );
};

const cColors: Record<string, string> = {
  Character: "text-accent-glow bg-accent/15 border-accent/20",
  Capacity: "text-emerald-glow bg-emerald/15 border-emerald/20",
  Capital: "text-gold-glow bg-gold/15 border-gold/20",
  Collateral: "text-rose-glow bg-rose/15 border-rose/20",
  Conditions: "text-[#ff6bb5] bg-[#e91e8c]/15 border-[#e91e8c]/20",
};

export default function NotesPage({ params }: { params: { caseId: string } }) {
  const [notes, setNotes] = useState<AnalystNote[]>([]);

  const refresh = () => listNotes(params.caseId).then(setNotes).catch(() => setNotes([]));

  useEffect(() => {
    refresh();
  }, [params.caseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="panel p-5 animate-slide-up">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Qualitative</p>
            <h2 className="mt-2 text-2xl font-semibold text-gradient">Analyst Notes</h2>
            <p className="mt-1 text-sm text-slate">
              Record observations from site visits, management meetings, and market feedback
            </p>
          </div>
          {notes.length > 0 && (
            <Badge tone="neutral">{notes.length} note{notes.length !== 1 ? "s" : ""}</Badge>
          )}
        </div>
      </div>

      {/* Form */}
      <div className="animate-slide-up stagger-1">
        <AnalystNoteForm
          caseId={params.caseId}
          onSubmit={async (payload) => {
            await createNote(params.caseId, payload);
            await refresh();
          }}
        />
      </div>

      {/* Notes list */}
      {notes.length === 0 && (
        <div className="panel p-5 text-center animate-fade-in">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-surface-200">
            <svg className="h-6 w-6 text-slate-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
            </svg>
          </div>
          <p className="mt-3 text-sm text-slate-dim">No notes recorded yet. Add your first observation above.</p>
        </div>
      )}

      <div className="space-y-3">
        {notes.map((note, i) => (
          <div
            key={note.id}
            className={`panel border-[#4a1530] p-5 transition-all duration-300 hover:border-[#7a2550] hover:bg-[#2d1420] animate-slide-up stagger-${Math.min(i + 2, 6)}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                {/* Meta row */}
                <div className="flex flex-wrap items-center gap-2">
                  {note.note_type && (
                    <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#4a1530] bg-[#2d1420] px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider text-slate">
                      {note.note_type.replace(/_/g, " ")}
                    </span>
                  )}
                  {note.affected_c && (
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider ${
                        cColors[note.affected_c] || "text-slate bg-[#2d1420] border-[#4a1530]"
                      }`}
                    >
                      {note.affected_c}
                    </span>
                  )}
                  <Badge tone={sentimentTone(note.sentiment)}>
                    <span className="flex items-center gap-1">
                      {sentimentIcon(note.sentiment)}
                      {note.sentiment || "neutral"}
                    </span>
                  </Badge>
                  {note.risk_adjustment !== null && note.risk_adjustment !== undefined && note.risk_adjustment !== 0 && (
                    <span
                      className={`text-[11px] font-bold ${
                        note.risk_adjustment > 0 ? "text-emerald-glow" : "text-rose-glow"
                      }`}
                    >
                      {note.risk_adjustment > 0 ? "+" : ""}
                      {note.risk_adjustment} risk adj.
                    </span>
                  )}
                </div>

                {/* Content */}
                <p className="mt-3 text-sm leading-relaxed text-slate-bright">{note.content}</p>

                {/* Timestamp */}
                <p className="mt-3 text-[11px] text-slate-dim">
                  {new Date(note.created_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await deleteNote(note.id);
                  await refresh();
                }}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                </svg>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
