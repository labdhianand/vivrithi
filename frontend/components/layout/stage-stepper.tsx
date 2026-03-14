"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { STAGES, cn } from "@/lib/utils";

export function StageStepper() {
  const pathname = usePathname();

  return (
    <div className="panel flex flex-wrap gap-2 p-2">
      {STAGES.map((stage, index) => {
        const active = pathname.startsWith(stage.href) || pathname === stage.href;
        const completed = index < STAGES.findIndex((s) => pathname.startsWith(s.href) || pathname === s.href);
        return (
          <Link
            key={stage.key}
            href={stage.href}
            className={cn(
              "flex items-center gap-2.5 rounded-xl px-3.5 py-2 transition-all duration-200",
              active
                ? "bg-accent/15 border border-accent/25 text-accent-glow"
                : completed
                  ? "bg-emerald/10 border border-emerald/15 text-emerald-glow"
                  : "border border-transparent text-slate-dim hover:text-slate hover:bg-white/[0.03]",
            )}
          >
            <span
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-lg text-[10px] font-bold",
                active
                  ? "bg-accent text-surface"
                  : completed
                    ? "bg-emerald/20 text-emerald"
                    : "bg-white/[0.06] text-slate-dim",
              )}
            >
              {completed ? (
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2.5 6l2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                index + 1
              )}
            </span>
            <span className="text-xs font-medium">{stage.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
