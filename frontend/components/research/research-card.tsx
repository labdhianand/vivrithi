import type { ResearchItem } from "@/lib/types";

import { SentimentBadge } from "@/components/research/sentiment-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const categoryIcons: Record<string, React.ReactNode> = {
  news: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 0 1-2.25 2.25M16.5 7.5V18a2.25 2.25 0 0 0 2.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 0 0 2.25 2.25h13.5M6 7.5h3v3H6v-3Z" />
    </svg>
  ),
  regulatory: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z" />
    </svg>
  ),
  financial: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  ),
  legal: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0 0 12 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 0 1-2.031.352 5.988 5.988 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971Zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0 2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 0 1-2.031.352 5.989 5.989 0 0 1-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971Z" />
    </svg>
  ),
};

const categoryColors: Record<string, string> = {
  news: "text-accent-glow bg-accent/15",
  regulatory: "text-gold-glow bg-gold/15",
  financial: "text-emerald-glow bg-emerald/15",
  legal: "text-rose-glow bg-rose/15",
  market: "text-blue-400 bg-blue-400/15",
  promoter: "text-rose-glow bg-rose/15",
  sector: "text-slate bg-surface-200",
};

const INDIAN_SOURCE_LABELS: Record<string, { label: string; badge: string }> = {
  "Reserve Bank of India": { label: "RBI", badge: "text-gold-glow" },
  "SEBI": { label: "SEBI", badge: "text-gold-glow" },
  "National Housing Bank": { label: "NHB", badge: "text-gold-glow" },
  "Ministry of Corporate Affairs": { label: "MCA", badge: "text-gold-glow" },
  "NSE India": { label: "NSE", badge: "text-emerald-glow" },
  "BSE India": { label: "BSE", badge: "text-emerald-glow" },
  "Trendlyne": { label: "Trendlyne", badge: "text-accent-glow" },
  "Moneycontrol": { label: "MC", badge: "text-accent-glow" },
  "Screener.in": { label: "Screener", badge: "text-accent-glow" },
  "National Company Law Tribunal": { label: "NCLT", badge: "text-rose-glow" },
  "NCLAT": { label: "NCLAT", badge: "text-rose-glow" },
  "IBBI": { label: "IBBI", badge: "text-rose-glow" },
};

export function ResearchCard({
  item,
  onDelete,
}: {
  item: ResearchItem;
  onDelete?: () => Promise<void>;
}) {
  const relevance = item.relevance_score ? parseFloat(item.relevance_score) : 0;
  const entityMatch = item.entity_match_score ? parseFloat(item.entity_match_score) : 0;
  const catKey = item.category?.toLowerCase() || "";
  const catColor = categoryColors[catKey] || "text-slate bg-surface-200";
  const catIcon = categoryIcons[catKey] || (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
  const verificationTone =
    item.verification_status === "verified"
      ? "success"
      : item.verification_status === "probable"
        ? "warn"
        : item.verification_status === "contextual"
          ? "info"
          : "default";
  const matchedTerms = (() => {
    if (!item.matched_terms) return [];
    try {
      const parsed = JSON.parse(item.matched_terms);
      return Array.isArray(parsed) ? parsed.slice(0, 4) : [];
    } catch {
      return [];
    }
  })();

  return (
    <div className="panel p-5 transition-all duration-300 hover:border-white/[0.12]">
      <div className="flex items-start gap-4">
        {/* Category icon */}
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${catColor}`}>
          {catIcon}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Badge row */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{item.category}</Badge>
            <SentimentBadge value={item.sentiment} />
            <Badge tone={item.severity === "high" ? "danger" : item.severity === "medium" ? "warn" : "default"}>
              {item.severity || "low"}
            </Badge>
            {item.affected_c && <Badge tone="info">{item.affected_c}</Badge>}
            {item.verification_status && <Badge tone={verificationTone}>{item.verification_status}</Badge>}
            {item.entity_scope && <Badge tone="neutral">{item.entity_scope}</Badge>}
          </div>

          {/* Title */}
          <h3 className="mt-3 text-base font-semibold text-slate-bright">
            {item.title || "Untitled finding"}
          </h3>

          {/* Summary */}
          <p className="mt-2 text-sm leading-relaxed text-slate">{item.summary}</p>

          {/* Impact */}
          {item.impact_description && (
            <p className="mt-2 text-sm text-slate-dim">{item.impact_description}</p>
          )}

          {(item.match_explanation || matchedTerms.length > 0) && (
            <div className="mt-3 rounded-xl border border-white/[0.06] bg-surface-200/50 p-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Entity Match</p>
              {item.match_explanation && <p className="mt-2 text-xs leading-relaxed text-slate">{item.match_explanation}</p>}
              {matchedTerms.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {matchedTerms.map((term) => (
                    <span
                      key={term}
                      className="rounded-md border border-white/[0.08] bg-surface-300/60 px-2 py-1 text-[11px] text-slate"
                    >
                      {term}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Relevance score bar */}
          {(relevance > 0 || entityMatch > 0) && (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {relevance > 0 && (
                <div>
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Relevance</p>
                    <span className="text-[11px] font-semibold text-slate-bright">{Math.round(relevance * 100)}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-accent to-accent-glow transition-all duration-500"
                      style={{ width: `${Math.min(relevance * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
              {entityMatch > 0 && (
                <div>
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Entity Match</p>
                    <span className="text-[11px] font-semibold text-slate-bright">{Math.round(entityMatch * 100)}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-surface-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-gold to-gold-glow transition-all duration-500"
                      style={{ width: `${Math.min(entityMatch * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Source URL + meta */}
          <div className="mt-4 flex flex-wrap items-center gap-4">
            {item.source_name && INDIAN_SOURCE_LABELS[item.source_name] && (
              <span className={`inline-flex items-center rounded-md border border-white/[0.08] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.15em] ${INDIAN_SOURCE_LABELS[item.source_name].badge}`}>
                {INDIAN_SOURCE_LABELS[item.source_name].label}
              </span>
            )}
            {item.source_url && (
              <a
                className="inline-flex items-center gap-1.5 text-xs font-medium text-accent-glow transition-colors hover:text-accent"
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                {item.source_name || "Open source"}
              </a>
            )}
            {item.published_date && (
              <span className="text-[11px] text-slate-dim">{item.published_date}</span>
            )}
          </div>
        </div>

        {/* Delete button */}
        {onDelete && (
          <Button variant="ghost" size="sm" onClick={onDelete} className="shrink-0">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </Button>
        )}
      </div>
    </div>
  );
}
