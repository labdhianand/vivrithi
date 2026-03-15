"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Command Center", icon: "grid" },
  { href: "/onboarding", label: "New Case", icon: "plus" },
  { href: "/cases", label: "Case Pipeline", icon: "layers" },
];

const icons: Record<string, React.ReactNode> = {
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
    <aside className="sticky top-5 flex h-[calc(100vh-2.5rem)] min-w-[260px] max-w-[260px] flex-col gap-6 overflow-hidden rounded-[28px] border border-white/[0.08] bg-surface-50/[0.88] p-5 shadow-panel backdrop-blur-2xl">
      {/* Brand */}
      <div>
        <div className="mb-4 flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.05]">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M9 1L16 5v8l-7 4-7-4V5l7-4z" stroke="#7AA0FF" strokeWidth="1.5" strokeLinejoin="round" />
              <path d="M9 9v8M9 9l7-4M9 9L2 5" stroke="#7AA0FF" strokeWidth="1.5" />
            </svg>
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-bright/[0.78]">Intelli-Credit</span>
        </div>
        <h1 className="font-serif text-[28px] leading-[1.05] text-slate-bright">
          Credit Decisioning<br />
          <span className="text-gradient">Engine</span>
        </h1>
      </div>

      {/* Navigation */}
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
                  ? "border border-white/[0.14] bg-white/[0.08] font-medium text-slate-bright"
                  : "text-slate hover:bg-white/[0.05] hover:text-slate-bright",
              )}
            >
              <span className={cn("transition-colors", active ? "text-accent-glow" : "text-slate-dim")}>
                {icons[link.icon]}
              </span>
              {link.label}
            </Link>
          );
        })}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Signal panel */}
      <div className="rounded-[22px] border border-white/[0.08] bg-gradient-to-br from-white/[0.06] to-accent/10 p-4">
        <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-accent-glow/80">
          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-glow-pulse" />
          AI Engine Active
        </div>
        <p className="mt-2.5 text-[13px] leading-relaxed text-slate-dim/95">
          Trace extracted values to source pages, auto-score with ML, and generate investment-grade CAMs.
        </p>
      </div>

      {/* Version */}
      <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-dim/50">
        v1.0 &middot; Powered by Gemini + GBM
      </div>
    </aside>
  );
}
