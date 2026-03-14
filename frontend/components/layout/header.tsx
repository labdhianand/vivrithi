"use client";

import { usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();

  const getTitle = () => {
    if (pathname === "/") return "Command Center";
    if (pathname === "/onboarding") return "Entity Onboarding";
    if (pathname === "/cases") return "Case Pipeline";
    if (pathname.includes("/upload")) return "Document Ingestion";
    if (pathname.includes("/classify")) return "Classification Review";
    if (pathname.includes("/extraction")) return "Data Extraction";
    if (pathname.includes("/schema")) return "Schema Configuration";
    if (pathname.includes("/analysis")) return "Credit Analysis";
    if (pathname.includes("/report")) return "CAM Report";
    if (pathname.includes("/cases/")) return "Case Overview";
    return "Workspace";
  };

  const getBreadcrumbs = () => {
    const parts = pathname.split("/").filter(Boolean);
    return parts.map((part) =>
      part.length > 20 ? `${part.slice(0, 8)}...` : part.replace(/-/g, " "),
    );
  };

  return (
    <header className="panel flex items-center justify-between p-4">
      <div>
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-slate-dim">
          {getBreadcrumbs().map((crumb, i) => (
            <span key={i} className="flex items-center gap-2">
              {i > 0 && <span className="text-white/20">/</span>}
              <span>{crumb}</span>
            </span>
          ))}
        </div>
        <h2 className="mt-1.5 text-xl font-semibold text-slate-bright">{getTitle()}</h2>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-xl border border-emerald/20 bg-emerald/10 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald animate-pulse" />
          <span className="text-xs text-emerald-glow">System Online</span>
        </div>
      </div>
    </header>
  );
}
