"use client";

import type { Recommendation } from "@/lib/types";

import { Badge } from "@/components/ui/badge";
import { EvidencePills } from "@/components/evidence/evidence-pills";
import { formatCurrency } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/*  Recommendation Panel  –  the HEADLINE verdict                     */
/* ------------------------------------------------------------------ */

type Tone = "success" | "warn" | "danger";

function decideTone(rec: string): Tone {
  if (rec === "approve") return "success";
  if (rec === "conditional_approve") return "warn";
  return "danger";
}

const TONE_STYLES: Record<
  Tone,
  {
    gradient: string;
    glow: string;
    accent: string;
    border: string;
    bg: string;
    shadow: string;
    label: string;
  }
> = {
  success: {
    gradient: "from-emerald/20 via-emerald/5 to-transparent",
    glow: "shadow-glow-emerald",
    accent: "#34d399",
    border: "border-emerald/25",
    bg: "rgba(16, 185, 129, 0.06)",
    shadow: "0 0 60px rgba(16, 185, 129, 0.15)",
    label: "Approved",
  },
  warn: {
    gradient: "from-gold/20 via-gold/5 to-transparent",
    glow: "shadow-glow-gold",
    accent: "#fbbf24",
    border: "border-gold/25",
    bg: "rgba(245, 158, 11, 0.06)",
    shadow: "0 0 60px rgba(245, 158, 11, 0.15)",
    label: "Conditional",
  },
  danger: {
    gradient: "from-rose/20 via-rose/5 to-transparent",
    glow: "shadow-glow-rose",
    accent: "#fb7185",
    border: "border-rose/25",
    bg: "rgba(244, 63, 94, 0.06)",
    shadow: "0 0 60px rgba(244, 63, 94, 0.15)",
    label: "Rejected",
  },
};

const TONE_BADGE: Record<Tone, "success" | "warn" | "danger"> = {
  success: "success",
  warn: "warn",
  danger: "danger",
};

export function RecommendationPanel({
  recommendation,
  caseId,
}: {
  recommendation: Recommendation;
  caseId: string;
}) {
  const tone = decideTone(recommendation.recommendation);
  const styles = TONE_STYLES[tone];

  return (
    <div className="animate-fade-in space-y-6">
      {/* ============================================================ */}
      {/* HERO VERDICT CARD                                            */}
      {/* ============================================================ */}
      <div
        className={`panel-glow relative overflow-hidden border ${styles.border} p-0`}
        style={{ boxShadow: styles.shadow }}
      >
        {/* Background gradient wash */}
        <div
          className={`absolute inset-0 bg-gradient-to-br ${styles.gradient} pointer-events-none`}
        />

        <div className="relative p-6 md:p-8">
          {/* Top row: label + risk grade */}
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                Credit Recommendation
              </div>
              <h2
                className="mt-2 text-3xl font-bold capitalize tracking-tight md:text-4xl"
                style={{ color: styles.accent }}
              >
                {recommendation.recommendation.replaceAll("_", " ")}
              </h2>
            </div>

            {/* Risk grade block */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                  Risk Grade
                </div>
                <div
                  className="mt-1 text-2xl font-bold tracking-wider md:text-3xl"
                  style={{ color: styles.accent }}
                >
                  {recommendation.risk_grade}
                </div>
              </div>
              <div
                className="h-12 w-px"
                style={{ backgroundColor: `${styles.accent}30` }}
              />
              <div className="text-right">
                <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                  Score
                </div>
                <div className="mt-1 text-2xl font-bold tabular-nums text-slate-bright md:text-3xl">
                  {recommendation.overall_score}
                  <span className="text-sm font-normal text-slate-dim">/100</span>
                </div>
              </div>
            </div>
          </div>

          {/* Decision reasoning */}
          <div className="mt-6 rounded-xl border border-white/[0.04] bg-surface-200/40 p-4">
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Decision Rationale
            </div>
            <p className="mt-2 text-[14px] leading-relaxed text-slate-bright/90">
              {recommendation.decision_reasoning}
            </p>
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* STAT BLOCKS ROW                                              */}
      {/* ============================================================ */}
      <div className="grid gap-3 sm:grid-cols-3">
        {/* Amount */}
        <div className="panel stagger-1 animate-slide-up p-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
              <svg className="h-4 w-4 text-accent-glow" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.75 2.75a.75.75 0 00-1.5 0v1.69L7.034 5.397a.75.75 0 00.932 1.176L10 5.06l2.034 1.513a.75.75 0 10.932-1.176L10.75 4.44V2.75z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Recommended Amount
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-gradient">
            {formatCurrency(recommendation.recommended_amount_crore)}
          </div>
        </div>

        {/* Rate */}
        <div className="panel stagger-2 animate-slide-up p-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold/10">
              <svg className="h-4 w-4 text-gold-glow" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Interest Rate
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-gradient-gold">
            {recommendation.recommended_rate_percent || "N/A"}
            {recommendation.recommended_rate_percent && (
              <span className="text-sm font-normal text-slate-dim">%</span>
            )}
          </div>
        </div>

        {/* Tenure */}
        <div className="panel stagger-3 animate-slide-up p-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald/10">
              <svg className="h-4 w-4 text-emerald-glow" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Tenure
            </div>
          </div>
          <div className="mt-3 text-2xl font-bold text-slate-bright">
            {recommendation.recommended_tenure_months || "N/A"}
            {recommendation.recommended_tenure_months && (
              <span className="ml-1 text-sm font-normal text-slate-dim">months</span>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* KEY STRENGTHS & RISKS                                        */}
      {/* ============================================================ */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Strengths */}
        <div className="panel stagger-4 animate-slide-up overflow-hidden border-t-2 border-t-emerald p-0">
          <div className="flex items-center gap-3 border-b border-white/[0.04] bg-emerald/[0.04] px-5 py-3.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald/15 text-[11px] font-bold text-emerald-glow">
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-slate-bright">Key Strengths</span>
            <span className="rounded-md bg-emerald/15 px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-emerald-glow">
              {recommendation.key_strengths.length}
            </span>
          </div>
          <div className="space-y-2 p-4">
            {recommendation.key_strengths.map((item, index) => (
              <div
                key={`${item.title}-${index}`}
                className="rounded-xl border border-white/[0.04] bg-emerald/[0.03] p-3.5 transition-colors hover:border-emerald/10"
              >
                <div className="flex items-start gap-2.5">
                  <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-glow" />
                  <div>
                    <div className="text-[13px] font-medium text-slate-bright">{item.title}</div>
                    <div className="mt-1 text-[12px] leading-relaxed text-slate/80">{item.detail}</div>
                    <EvidencePills refs={item.evidence_refs} caseId={caseId} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risks */}
        <div className="panel stagger-5 animate-slide-up overflow-hidden border-t-2 border-t-rose p-0">
          <div className="flex items-center gap-3 border-b border-white/[0.04] bg-rose/[0.04] px-5 py-3.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose/15 text-[11px] font-bold text-rose-glow">
              <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-slate-bright">Key Risks</span>
            <span className="rounded-md bg-rose/15 px-1.5 py-0.5 text-[10px] font-bold tabular-nums text-rose-glow">
              {recommendation.key_risks.length}
            </span>
          </div>
          <div className="space-y-2 p-4">
            {recommendation.key_risks.map((item, index) => (
              <div
                key={`${item.title}-${index}`}
                className="rounded-xl border border-white/[0.04] bg-rose/[0.03] p-3.5 transition-colors hover:border-rose/10"
              >
                <div className="flex items-start gap-2.5">
                  <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-glow" />
                  <div>
                    <div className="text-[13px] font-medium text-slate-bright">{item.title}</div>
                    <div className="mt-1 text-[12px] leading-relaxed text-slate/80">{item.detail}</div>
                    <EvidencePills refs={item.evidence_refs} caseId={caseId} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* CONDITIONS & COVENANTS                                       */}
      {/* ============================================================ */}
      {(recommendation.conditions_precedent.length > 0 ||
        recommendation.conditions_subsequent.length > 0 ||
        recommendation.monitoring_covenants.length > 0) && (
        <div className="panel stagger-6 animate-slide-up p-0">
          <div className="border-b border-white/[0.04] px-5 py-3.5">
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Conditions &amp; Covenants
            </div>
          </div>

          <div className="grid gap-0 divide-y divide-white/[0.04] md:grid-cols-3 md:divide-x md:divide-y-0">
            {/* Conditions Precedent */}
            {recommendation.conditions_precedent.length > 0 && (
              <div className="p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Badge tone="warn">CP</Badge>
                  <span className="text-[12px] font-semibold text-slate-bright">
                    Conditions Precedent
                  </span>
                </div>
                <ul className="space-y-2">
                  {recommendation.conditions_precedent.map((cp, i) => (
                    <li key={i} className="flex items-start gap-2 text-[12px] leading-relaxed text-slate/90">
                      <span className="mt-1 block h-1 w-1 shrink-0 rounded-full bg-gold-glow/60" />
                      {cp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Conditions Subsequent */}
            {recommendation.conditions_subsequent.length > 0 && (
              <div className="p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Badge tone="info">CS</Badge>
                  <span className="text-[12px] font-semibold text-slate-bright">
                    Conditions Subsequent
                  </span>
                </div>
                <ul className="space-y-2">
                  {recommendation.conditions_subsequent.map((cs, i) => (
                    <li key={i} className="flex items-start gap-2 text-[12px] leading-relaxed text-slate/90">
                      <span className="mt-1 block h-1 w-1 shrink-0 rounded-full bg-blue-400/60" />
                      {cs}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Monitoring Covenants */}
            {recommendation.monitoring_covenants.length > 0 && (
              <div className="p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Badge tone="neutral">MC</Badge>
                  <span className="text-[12px] font-semibold text-slate-bright">
                    Monitoring Covenants
                  </span>
                </div>
                <ul className="space-y-2">
                  {recommendation.monitoring_covenants.map((mc, i) => (
                    <li key={i} className="flex items-start gap-2 text-[12px] leading-relaxed text-slate/90">
                      <span className="mt-1 block h-1 w-1 shrink-0 rounded-full bg-slate-dim/60" />
                      {mc}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
