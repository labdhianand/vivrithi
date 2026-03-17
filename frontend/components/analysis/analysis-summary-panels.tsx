"use client";

import type { AnalysisSummary } from "@/lib/types";

import { Badge } from "@/components/ui/badge";

function parseMatchedTerms(value?: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.slice(0, 3) : [];
  } catch {
    return [];
  }
}

export function AnalysisSummaryPanels({ summary }: { summary: AnalysisSummary }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <div className="panel p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Coverage</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-bright">Missing Critical Fields</h3>
          </div>
          <Badge tone={summary.missing_required_fields.length > 0 ? "danger" : "success"}>
            {summary.missing_required_fields.length}
          </Badge>
        </div>
        <div className="mt-4 space-y-3">
          {summary.missing_required_fields.length === 0 ? (
            <p className="text-sm text-slate">Required schema coverage looks complete for the latest processed documents.</p>
          ) : (
            summary.missing_required_fields.slice(0, 8).map((field) => (
              <div key={`${field.document_category}-${field.field_key}`} className="rounded-xl border border-red-800 bg-red-950/40 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="danger">{field.document_category}</Badge>
                  {field.document_name && <Badge tone="neutral">{field.document_name}</Badge>}
                </div>
                <p className="mt-2 text-sm text-slate-bright">{field.field_label}</p>
                <p className="mt-1 text-xs text-slate-dim">Field key: {field.field_key}</p>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="panel p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Triangulation</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-bright">Cross-Document Contradictions</h3>
          </div>
          <Badge tone={summary.contradictions.length > 0 ? "warn" : "success"}>
            {summary.contradictions.length}
          </Badge>
        </div>
        <div className="mt-4 space-y-3">
          {summary.contradictions.length === 0 ? (
            <p className="text-sm text-slate">No explicit cross-document mismatches are currently recorded.</p>
          ) : (
            summary.contradictions.slice(0, 6).map((item) => (
              <div key={item.id} className="rounded-xl border border-amber-800 bg-amber-950/40 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="warn">{item.check_name}</Badge>
                  {item.doc_a && <Badge tone="neutral">{item.doc_a}</Badge>}
                  {item.doc_b && <Badge tone="neutral">{item.doc_b}</Badge>}
                </div>
                {item.note && <p className="mt-2 text-sm text-slate">{item.note}</p>}
                {(item.value_a || item.value_b) && (
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    {item.value_a && <p className="text-xs text-slate-dim">A: {item.value_a}</p>}
                    {item.value_b && <p className="text-xs text-slate-dim">B: {item.value_b}</p>}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="panel p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Research</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-bright">Verified External Signals</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(summary.research_digest.counts_by_status).map(([status, count]) => (
              <Badge key={status} tone="neutral">
                {status}: {count}
              </Badge>
            ))}
          </div>
        </div>
        <div className="mt-4 space-y-3">
          {summary.research_digest.verified_borrower_items.length === 0 ? (
            <p className="text-sm text-slate">No borrower-specific verified research findings are currently available.</p>
          ) : (
            summary.research_digest.verified_borrower_items.map((item) => (
              <div key={item.id} className="rounded-xl border border-[#4a1530] bg-[#2d1420] p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={item.severity === "high" ? "danger" : item.severity === "medium" ? "warn" : "default"}>
                    {item.category}
                  </Badge>
                  {item.verification_status && <Badge tone="success">{item.verification_status}</Badge>}
                  {item.entity_scope && <Badge tone="neutral">{item.entity_scope}</Badge>}
                </div>
                <p className="mt-2 text-sm text-slate-bright">{item.title}</p>
                {item.match_explanation && <p className="mt-1 text-xs text-slate-dim">{item.match_explanation}</p>}
                {parseMatchedTerms(item.matched_terms).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {parseMatchedTerms(item.matched_terms).map((term) => (
                      <span key={term} className="rounded-md border border-[#4a1530] bg-[#3d1a2a] px-2 py-1 text-[11px] text-slate">
                        {term}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="panel p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Primary Insight</p>
            <h3 className="mt-2 text-lg font-semibold text-slate-bright">Analyst Overlay</h3>
          </div>
          <Badge tone="info">{summary.note_impacts.length}</Badge>
        </div>
        <div className="mt-4 space-y-3">
          {summary.note_impacts.length === 0 ? (
            <p className="text-sm text-slate">No analyst observations have been added yet.</p>
          ) : (
            summary.note_impacts.slice(0, 6).map((note) => (
              <div key={note.id} className="rounded-xl border border-[#4a1530] bg-[#2d1420] p-3">
                <div className="flex flex-wrap items-center gap-2">
                  {note.note_type && <Badge tone="neutral">{note.note_type.replace(/_/g, " ")}</Badge>}
                  {note.affected_c && <Badge tone="info">{note.affected_c}</Badge>}
                  {note.sentiment && <Badge tone={note.sentiment === "negative" ? "danger" : note.sentiment === "positive" ? "success" : "neutral"}>{note.sentiment}</Badge>}
                  {typeof note.risk_adjustment === "number" && (
                    <Badge tone={note.risk_adjustment < 0 ? "danger" : note.risk_adjustment > 0 ? "success" : "neutral"}>
                      {note.risk_adjustment > 0 ? "+" : ""}
                      {note.risk_adjustment}
                    </Badge>
                  )}
                </div>
                <p className="mt-2 text-sm text-slate">{note.content}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
