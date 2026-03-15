import type { ResearchItem } from "@/lib/types";

function riskClass(risk?: string | null) {
  if (risk === "high") return "bg-red-100 text-red-700";
  if (risk === "medium") return "bg-amber-100 text-amber-700";
  return "bg-emerald-100 text-emerald-700";
}

export function ResearchCard({ item }: { item: ResearchItem }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">Firecrawl</span>
        {item.severity ? (
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${riskClass(item.severity)}`}>
            {item.severity.charAt(0).toUpperCase() + item.severity.slice(1)}
          </span>
        ) : null}
      </div>

      <h3 className="mt-4 text-base font-semibold text-slate-900">{item.title || "Untitled finding"}</h3>

      {item.source_url ? (
        <a
          href={item.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block truncate text-sm text-blue-600 underline-offset-2 hover:underline"
        >
          {item.source_url}
        </a>
      ) : null}

      <p className="mt-3 text-sm leading-6 text-slate-600">{item.summary || "No summary available."}</p>
    </div>
  );
}
