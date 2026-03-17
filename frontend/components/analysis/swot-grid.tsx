"use client";

import type { SWOT, SWOTItem } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  SWOT Grid  –  premium 2x2 strategic analysis                     */
/* ------------------------------------------------------------------ */

interface QuadrantConfig {
  key: keyof SWOT;
  label: string;
  icon: string;
  borderColor: string;
  accentColor: string;
  glowColor: string;
  bgTint: string;
  dotColor: string;
}

const QUADRANTS: QuadrantConfig[] = [
  {
    key: "strengths",
    label: "Strengths",
    icon: "S",
    borderColor: "border-t-emerald",
    accentColor: "#34d399",
    glowColor: "rgba(16, 185, 129, 0.06)",
    bgTint: "rgba(16, 185, 129, 0.04)",
    dotColor: "bg-emerald-glow",
  },
  {
    key: "weaknesses",
    label: "Weaknesses",
    icon: "W",
    borderColor: "border-t-rose",
    accentColor: "#fb7185",
    glowColor: "rgba(244, 63, 94, 0.06)",
    bgTint: "rgba(244, 63, 94, 0.04)",
    dotColor: "bg-rose-glow",
  },
  {
    key: "opportunities",
    label: "Opportunities",
    icon: "O",
    borderColor: "border-t-accent",
    accentColor: "#e91e8c",
    glowColor: "rgba(233, 30, 140, 0.06)",
    bgTint: "rgba(233, 30, 140, 0.04)",
    dotColor: "bg-accent-glow",
  },
  {
    key: "threats",
    label: "Threats",
    icon: "T",
    borderColor: "border-t-gold",
    accentColor: "#fbbf24",
    glowColor: "rgba(245, 158, 11, 0.06)",
    bgTint: "rgba(245, 158, 11, 0.04)",
    dotColor: "bg-gold-glow",
  },
];

function SwotItem({ item, config, index }: { item: SWOTItem; config: QuadrantConfig; index: number }) {
  return (
    <div
      className={`stagger-${Math.min(index + 1, 6)} animate-slide-up rounded-xl border border-[#4a1530] p-3.5 transition-colors hover:border-[#7a2550]`}
      style={{ backgroundColor: config.bgTint }}
    >
      <div className="flex items-start gap-2.5">
        {/* Accent dot */}
        <div
          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
          style={{ backgroundColor: config.accentColor }}
        />
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-medium leading-snug text-slate-bright">
            {item.point}
          </div>
          <div className="mt-1.5 text-[12px] leading-relaxed text-slate/80">
            {item.evidence}
          </div>
          {item.source && (
            <div className="mt-2 flex items-center gap-1.5">
              <svg className="h-3 w-3 text-slate-dim/60" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 1v2a3 3 0 003 3h2M8 15V9m0 0l-3 3m3-3l3 3M14 7V4.5a1.5 1.5 0 00-1.5-1.5H10" />
              </svg>
              <span className="text-[10px] font-medium tracking-wide text-slate-dim/70">
                {item.source}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function SwotGrid({ swot }: { swot: SWOT }) {
  return (
    <div className="animate-fade-in">
      {/* Section header */}
      <div className="mb-5">
        <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
          Strategic Analysis
        </div>
        <h3 className="mt-1 text-lg font-semibold text-gradient">SWOT Assessment</h3>
      </div>

      {/* 2x2 Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {QUADRANTS.map((config) => (
          <div
            key={config.key}
            className={`panel overflow-hidden border border-[#4a1530] border-t-2 p-0 ${config.borderColor}`}
          >
            <div
              className="flex items-center gap-3 border-b border-[#4a1530] px-5 py-3.5"
              style={{ backgroundColor: config.glowColor }}
            >
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg text-[11px] font-bold"
                style={{
                  backgroundColor: `${config.accentColor}20`,
                  color: config.accentColor,
                }}
              >
                {config.icon}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-slate-bright">
                  {config.label}
                </span>
                <span
                  className="rounded-md px-1.5 py-0.5 text-[10px] font-bold tabular-nums"
                  style={{
                    backgroundColor: `${config.accentColor}15`,
                    color: config.accentColor,
                  }}
                >
                  {swot[config.key].length}
                </span>
              </div>
            </div>

            {/* Items */}
            <div className="space-y-2 p-4">
              {swot[config.key].length === 0 ? (
                <div className="py-6 text-center text-[12px] text-slate-dim">
                  No items identified
                </div>
              ) : (
                swot[config.key].map((item: SWOTItem, index: number) => (
                  <SwotItem key={`${item.point}-${index}`} item={item} config={config} index={index} />
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
