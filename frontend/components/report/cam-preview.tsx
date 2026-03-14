import type { ReportRecord } from "@/lib/types";
import { EvidencePills } from "@/components/evidence/evidence-pills";

export function CamPreview({ report }: { report: ReportRecord }) {
  const sections = report.sections || [];

  return (
    <div className="space-y-1">
      {/* Document wrapper with dark professional appearance */}
      <div className="panel p-5">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15">
            <svg className="h-4.5 w-4.5 text-accent-glow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-bright">Document Preview</h3>
            <p className="text-[11px] text-slate-dim">
              {sections.length} section{sections.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((section, i) => (
            <div key={section.id}>
              {/* Section divider (not on first) */}
              {i > 0 && <div className="mb-6 h-px bg-white/[0.06]" />}

              {/* Section header */}
              <div className="mb-4 flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-surface-200 text-[10px] font-bold text-slate-dim">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                    Section {section.id}
                  </p>
                  <h3 className="mt-1 text-lg font-semibold text-slate-bright">{section.title}</h3>
                </div>
              </div>

              {/* Section content */}
              <div className="ml-9 rounded-xl bg-surface-200/50 px-5 py-4">
                <div className="whitespace-pre-wrap text-sm leading-7 text-slate">
                  {section.content_markdown}
                </div>
                <EvidencePills refs={section.evidence_refs} caseId={report.case_id} />
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        {sections.length > 0 && (
          <>
            <div className="mt-8 h-px bg-white/[0.06]" />
            <div className="mt-4 flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                Intelli-Credit CAM
              </p>
              <p className="text-[10px] text-slate-dim">
                Generated {new Date(report.created_at).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
