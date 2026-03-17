import type { ResearchItem } from "@/lib/types";

function riskClass(risk?: string | null) {
  if (risk === "high") return "bg-red-950 text-red-300";
  if (risk === "medium") return "bg-amber-950 text-amber-300";
  return "bg-green-950 text-green-300";
}

export function ResearchCard({ item }: { item: ResearchItem }) {
  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-5 shadow-card">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-[#3d1a2a] px-3 py-1 text-xs font-medium text-[#ff6bb5]">Firecrawl</span>
        {item.severity ? (
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${riskClass(item.severity)}`}>
            {item.severity.charAt(0).toUpperCase() + item.severity.slice(1)}
          </span>
        ) : null}
      </div>

      <h3 className="mt-4 text-base font-semibold text-[#fce4ec]">{item.title || "Untitled finding"}</h3>

      {item.source_url ? (
        <a
          href={item.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block truncate text-sm text-[#ff6bb5] underline-offset-2 hover:text-[#f48fb1] hover:underline"
        >
          {item.source_url}
        </a>
      ) : null}

      <p className="mt-3 text-sm leading-6 text-[#f48fb1]">{item.summary || "No summary available."}</p>
    </div>
  );
}
