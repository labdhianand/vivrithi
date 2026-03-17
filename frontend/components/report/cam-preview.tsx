import type { ReportRecord } from "@/lib/types";
import { EvidencePills } from "@/components/evidence/evidence-pills";

type MarkdownBlock = {
  kind: "heading" | "subheading" | "bullet" | "paragraph";
  text: string;
};

function cleanLine(text: string) {
  return text.replace(/\s+/g, " ").trim();
}

function parseMarkdown(content: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = [];
  const paragraphLines: string[] = [];

  const flushParagraph = () => {
    if (paragraphLines.length) {
      blocks.push({ kind: "paragraph", text: cleanLine(paragraphLines.join(" ")) });
      paragraphLines.length = 0;
    }
  };

  for (const rawLine of content.split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      continue;
    }
    if (line.startsWith("#### ")) {
      flushParagraph();
      blocks.push({ kind: "subheading", text: line.slice(5).trim() });
      continue;
    }
    if (/^#{1,3}\s+/.test(line)) {
      flushParagraph();
      blocks.push({ kind: "heading", text: line.replace(/^#{1,6}\s+/, "").trim() });
      continue;
    }
    if (line.startsWith("- ")) {
      flushParagraph();
      blocks.push({ kind: "bullet", text: line.slice(2).trim() });
      continue;
    }
    paragraphLines.push(line);
  }

  flushParagraph();
  return blocks;
}

function prettifyId(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function anchorForSection(sectionId: string, index: number) {
  return `${sectionId || "section"}-${index + 1}`;
}

function firstSectionSnippet(report: ReportRecord) {
  const first = report.sections?.[0]?.content_markdown || "";
  const blocks = parseMarkdown(first);
  return blocks.find((block) => block.kind === "paragraph" || block.kind === "bullet")?.text || "Generated credit memo draft ready for review and export.";
}

function splitLabelValue(text: string) {
  const colonIndex = text.indexOf(":");
  if (colonIndex === -1) {
    return null;
  }
  const label = text.slice(0, colonIndex).trim();
  const value = text.slice(colonIndex + 1).trim();
  if (!label || !value) {
    return null;
  }
  if (label.length > 34 || label.includes("]")) {
    return null;
  }
  return { label, value };
}

function formatReportDate(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function CamPreview({ report }: { report: ReportRecord }) {
  const sections = report.sections || [];
  const summarySnippet = firstSectionSnippet(report);

  return (
    <div className="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="space-y-4 xl:sticky xl:top-5 xl:self-start">
        <div className="panel p-5">
          <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Report Navigator</p>
          <h3 className="mt-2 font-serif text-2xl text-slate-bright">Memo Draft</h3>
          <p className="mt-2 text-sm leading-6 text-slate">
            Review the section flow here, then download the fully formatted DOCX or PDF for submission.
          </p>

          <div className="mt-5 grid gap-3">
            <div className="rounded-2xl border border-[#4a1530] bg-[#2d1420] p-3.5">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Sections</p>
              <p className="mt-2 text-2xl font-semibold text-gradient">{sections.length}</p>
            </div>
            <div className="rounded-2xl border border-[#4a1530] bg-[#2d1420] p-3.5">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-dim">Generated</p>
              <p className="mt-2 text-sm font-medium text-slate-bright">{formatReportDate(report.created_at)}</p>
            </div>
          </div>
        </div>

        <div className="panel p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Contents</p>
              <p className="mt-1 text-sm text-slate">Jump directly into a CAM section.</p>
            </div>
            <div className="rounded-full border border-[#4a1530] bg-[#2d1420] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-dim">
              {sections.length}
            </div>
          </div>

          <div className="mt-4 space-y-2">
            {sections.map((section, index) => (
              <a
                key={section.id}
                href={`#${anchorForSection(section.id, index)}`}
                className="group flex items-start gap-3 rounded-xl border border-[#4a1530] bg-[#2d1420]/70 px-3 py-2.5 transition-all duration-200 hover:border-[#7a2550] hover:bg-[#2d1420]"
              >
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-surface-100 text-[10px] font-bold text-slate-dim group-hover:text-accent-glow">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-bright">{section.title}</p>
                  <p className="mt-0.5 truncate text-[11px] text-slate-dim">{prettifyId(section.id)}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      </aside>

      <div className="panel overflow-hidden p-0">
        <div className="border-b border-[#4a1530] bg-[#2d1420] px-5 py-4 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-slate-dim">Report Preview</p>
              <h3 className="mt-1 font-serif text-2xl text-slate-bright">Credit Appraisal Memo</h3>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-[#4a1530] bg-[#3d1a2a] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-dim">
                Memo-style preview
              </span>
              <span className="rounded-full border border-[#4a1530] bg-[#3d1a2a] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-dim">
                {sections.length} sections
              </span>
            </div>
          </div>
        </div>

        <div className="bg-[radial-gradient(circle_at_top,_rgba(233,30,140,0.12),_transparent_35%),linear-gradient(180deg,_rgba(255,255,255,0.02),_rgba(255,255,255,0))] p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-4xl rounded-[28px] border border-[#4a1530] bg-[#1f0d16] text-[#fce4ec] shadow-[0_24px_80px_rgba(26,8,16,0.45)]">
            <div className="border-b border-[#4a1530] px-6 py-8 sm:px-10">
              <p className="text-center text-[11px] font-semibold uppercase tracking-[0.35em] text-[#ad6883]">
                Intelli-Credit Copilot
              </p>
              <h2 className="mt-4 text-center font-serif text-4xl leading-tight text-[#fce4ec] sm:text-[2.8rem]">
                Credit Appraisal Memo
              </h2>
              <p className="mt-3 text-center text-base text-[#f48fb1]">{summarySnippet}</p>

              <div className="mt-6 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-[#4a1530] bg-[#2d1420] p-4">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#ad6883]">Prepared</p>
                  <p className="mt-2 font-serif text-lg text-[#fce4ec]">{formatReportDate(report.created_at)}</p>
                </div>
                <div className="rounded-2xl border border-[#4a1530] bg-[#2d1420] p-4">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#ad6883]">Sections</p>
                  <p className="mt-2 font-serif text-lg text-[#fce4ec]">{sections.length}</p>
                </div>
                <div className="rounded-2xl border border-[#4a1530] bg-[#2d1420] p-4">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#ad6883]">Format</p>
                  <p className="mt-2 font-serif text-lg text-[#fce4ec]">CAM Draft</p>
                </div>
              </div>
            </div>

            <div className="px-6 py-6 sm:px-10 sm:py-8">
              {sections.map((section, index) => (
                <section
                  key={section.id}
                  id={anchorForSection(section.id, index)}
                  className={`py-8 ${index > 0 ? "border-t border-[#4a1530]" : "pt-0"}`}
                >
                  <div className="flex flex-wrap items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[#7a2550] bg-[#3d1a2a] text-sm font-semibold text-[#fce4ec]">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#ad6883]">
                        {prettifyId(section.id)}
                      </p>
                      <h3 className="mt-2 font-serif text-3xl leading-tight text-[#fce4ec]">
                        {section.title}
                      </h3>
                    </div>
                  </div>

                  <div className="mt-6 space-y-4">
                    {parseMarkdown(section.content_markdown).map((block, blockIndex) => {
                      if (block.kind === "heading") {
                        return (
                          <h4 key={blockIndex} className="font-serif text-2xl text-[#fce4ec]">
                            {block.text}
                          </h4>
                        );
                      }

                      if (block.kind === "subheading") {
                        return (
                          <h5 key={blockIndex} className="text-sm font-semibold uppercase tracking-[0.24em] text-[#ad6883]">
                            {block.text}
                          </h5>
                        );
                      }

                      if (block.kind === "bullet") {
                        const pair = splitLabelValue(block.text);
                        if (pair) {
                          return (
                            <div
                              key={blockIndex}
                              className="grid gap-2 rounded-2xl border border-[#4a1530] bg-[#2d1420] px-4 py-3 md:grid-cols-[220px_minmax(0,1fr)]"
                            >
                              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#ad6883]">
                                {pair.label}
                              </div>
                              <div className="text-[15px] leading-7 text-[#fce4ec]">{pair.value}</div>
                            </div>
                          );
                        }

                        return (
                          <div key={blockIndex} className="flex gap-3 rounded-2xl border border-[#4a1530] bg-[#2d1420] px-4 py-3">
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#ff6bb5]" />
                            <p className="text-[15px] leading-7 text-[#fce4ec]">{block.text}</p>
                          </div>
                        );
                      }

                      return (
                        <p key={blockIndex} className="text-[15px] leading-8 text-[#fce4ec]">
                          {block.text}
                        </p>
                      );
                    })}
                  </div>

                  <div className="mt-5 rounded-2xl border border-[#4a1530] bg-[#2d1420] px-4 py-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#ad6883]">Evidence Trail</p>
                    <EvidencePills refs={section.evidence_refs} caseId={report.case_id} tone="light" />
                  </div>
                </section>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
