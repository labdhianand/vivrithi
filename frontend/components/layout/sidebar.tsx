"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Command Center", icon: "grid" },
  { href: "/onboarding", label: "New Case", icon: "plus" },
  { href: "/cases", label: "Case Pipeline", icon: "layers" },
];

const icons: Record<string, ReactNode> = {
  grid: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="1" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="1" y="9" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <rect x="9" y="9" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  ),
  plus: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  ),
  layers: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 6l6-3 6 3-6 3-6-3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M2 8.5l6 3 6-3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M2 11l6 3 6-3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  ),
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-5 flex h-[calc(100vh-2.5rem)] min-w-[260px] max-w-[260px] flex-col gap-6 overflow-hidden rounded-[28px] border border-[#4a1530] bg-[#1f0d16] p-5 shadow-panel backdrop-blur-2xl">
      <div>
        <div className="mb-4 flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[#4a1530] bg-[#2d1420] text-[#e91e8c]">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 1L16 5v8l-7 4-7-4V5l7-4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M9 9v8M9 9l7-4M9 9L2 5" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#f48fb1]">Intelli-Credit</span>
        </div>
        <h1 className="font-serif text-[28px] leading-[1.05] text-[#fce4ec]">
          Credit Decisioning
          <br />
          <span className="text-gradient">Engine</span>
        </h1>
      </div>

      <nav className="flex flex-col gap-1.5">
        {links.map((link) => {
          const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(`${link.href}/`));
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm transition-all duration-200",
                active
                  ? "border border-[#7a2550] bg-[#3d1a2a] font-medium text-[#e91e8c]"
                  : "text-[#ad6883] hover:bg-[#2d1420] hover:text-[#f48fb1]",
              )}
            >
              <span className={cn("transition-colors", active ? "text-[#e91e8c]" : "text-[#ad6883]")}>{icons[link.icon]}</span>
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex-1" />

      <div className="rounded-[22px] border border-[#4a1530] bg-gradient-to-br from-[#2d1420] to-[#3d1a2a] p-4">
        <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-[#ff6bb5]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#e91e8c] animate-glow-pulse" />
          AI Engine Active
        </div>
        <p className="mt-2.5 text-[13px] leading-relaxed text-[#ad6883]">
          Trace extracted values to source pages, auto-score with ML, and generate investment-grade CAMs.
        </p>
      </div>

      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-[#ad6883]">v1.0 · Powered by Gemini + GBM</div>
    </aside>
  );
}
