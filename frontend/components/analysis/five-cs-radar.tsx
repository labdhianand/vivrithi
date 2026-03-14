"use client";

import type { FiveCs } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Five Cs Radar  –  CSS-only SVG pentagon chart                     */
/* ------------------------------------------------------------------ */

const CX = 150;
const CY = 155;
const MAX_R = 110;
const GRID_LEVELS = [20, 40, 60, 80, 100];
const LABELS = ["Character", "Capacity", "Capital", "Collateral", "Conditions"] as const;
const ANGLES = [-90, -18, 54, 126, 198]; // degrees, starting top-center

function vertex(angleDeg: number, radius: number) {
  const rad = (Math.PI / 180) * angleDeg;
  return { x: CX + Math.cos(rad) * radius, y: CY + Math.sin(rad) * radius };
}

function polygon(angleDeg: number[], values: number[]) {
  return angleDeg
    .map((a, i) => {
      const r = (values[i] / 100) * MAX_R;
      const { x, y } = vertex(a, r);
      return `${x},${y}`;
    })
    .join(" ");
}

function gridPolygon(angleDeg: number[], level: number) {
  return angleDeg
    .map((a) => {
      const r = (level / 100) * MAX_R;
      const { x, y } = vertex(a, r);
      return `${x},${y}`;
    })
    .join(" ");
}

function scoreColor(score: number) {
  if (score >= 70) return "#34d399";
  if (score >= 50) return "#fbbf24";
  return "#fb7185";
}

export function FiveCsRadar({ data }: { data: FiveCs }) {
  const values = [
    data.character.score,
    data.capacity.score,
    data.capital.score,
    data.collateral.score,
    data.conditions.score,
  ];

  const overallColor = scoreColor(data.overall_score);

  return (
    <div className="panel-glow animate-fade-in p-5">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
            Five Cs Analysis
          </div>
          <h3 className="mt-1 text-lg font-semibold text-gradient">
            Credit Profile Radar
          </h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
              Overall
            </div>
            <div className="text-xl font-bold" style={{ color: overallColor }}>
              {data.overall_score}
            </div>
          </div>
          <div
            className="flex h-10 items-center rounded-lg border px-3 text-sm font-bold uppercase tracking-wider"
            style={{
              borderColor: `${overallColor}33`,
              backgroundColor: `${overallColor}15`,
              color: overallColor,
            }}
          >
            {data.risk_grade}
          </div>
        </div>
      </div>

      {/* SVG Radar */}
      <svg viewBox="0 0 300 310" className="mx-auto h-[300px] w-full max-w-[340px]">
        <defs>
          {/* Glow filter for the data polygon */}
          <filter id="radar-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Radial gradient for data fill */}
          <radialGradient id="radar-fill" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.08" />
          </radialGradient>
          {/* Dot glow */}
          <filter id="dot-glow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
          </filter>
        </defs>

        {/* Grid lines */}
        {GRID_LEVELS.map((level) => (
          <polygon
            key={`grid-${level}`}
            points={gridPolygon(ANGLES, level)}
            fill="none"
            stroke="rgba(148, 163, 184, 0.08)"
            strokeWidth={level === 100 ? "1" : "0.5"}
          />
        ))}

        {/* Axis lines from center to each vertex */}
        {ANGLES.map((a, i) => {
          const { x, y } = vertex(a, MAX_R);
          return (
            <line
              key={`axis-${i}`}
              x1={CX}
              y1={CY}
              x2={x}
              y2={y}
              stroke="rgba(148, 163, 184, 0.06)"
              strokeWidth="0.5"
            />
          );
        })}

        {/* Grid level labels (right side) */}
        {GRID_LEVELS.map((level) => {
          const { y } = vertex(-90, (level / 100) * MAX_R);
          return (
            <text
              key={`label-${level}`}
              x={CX + 8}
              y={y + 3}
              fontSize="8"
              fill="rgba(148, 163, 184, 0.3)"
              fontFamily="inherit"
            >
              {level}
            </text>
          );
        })}

        {/* Data polygon glow layer */}
        <polygon
          points={polygon(ANGLES, values)}
          fill="url(#radar-fill)"
          stroke="#22d3ee"
          strokeWidth="1.5"
          opacity="0.5"
          filter="url(#radar-glow)"
        />

        {/* Data polygon */}
        <polygon
          points={polygon(ANGLES, values)}
          fill="url(#radar-fill)"
          stroke="#22d3ee"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* Data points + score labels at each vertex */}
        {ANGLES.map((a, i) => {
          const r = (values[i] / 100) * MAX_R;
          const { x, y } = vertex(a, r);
          const dotColor = scoreColor(values[i]);
          return (
            <g key={`point-${i}`}>
              {/* Glow behind dot */}
              <circle cx={x} cy={y} r="6" fill={dotColor} opacity="0.3" filter="url(#dot-glow)" />
              {/* Dot */}
              <circle cx={x} cy={y} r="3.5" fill={dotColor} stroke="#080d1a" strokeWidth="1.5" />
              {/* Score at vertex */}
              <text
                x={x}
                y={y - 10}
                textAnchor="middle"
                fontSize="10"
                fontWeight="700"
                fill={dotColor}
                fontFamily="inherit"
              >
                {values[i]}
              </text>
            </g>
          );
        })}

        {/* Category labels around the pentagon */}
        {ANGLES.map((a, i) => {
          const labelR = MAX_R + 28;
          const { x, y } = vertex(a, labelR);
          return (
            <text
              key={`cat-${i}`}
              x={x}
              y={y + 4}
              textAnchor="middle"
              fontSize="10"
              fontWeight="600"
              fill="#94a3b8"
              fontFamily="inherit"
              letterSpacing="0.05em"
            >
              {LABELS[i]}
            </text>
          );
        })}
      </svg>

      {/* Score summary row */}
      <div className="mt-4 grid grid-cols-5 gap-1">
        {LABELS.map((label, i) => (
          <div
            key={label}
            className={`stagger-${i + 1} animate-slide-up rounded-lg border border-white/[0.04] bg-surface-200/60 p-2 text-center`}
          >
            <div className="text-[9px] font-bold uppercase tracking-[0.2em] text-slate-dim">
              {label.slice(0, 4)}
            </div>
            <div className="mt-0.5 text-sm font-bold" style={{ color: scoreColor(values[i]) }}>
              {values[i]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
