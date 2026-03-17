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
    return parts.map((part) => (part.length > 20 ? `${part.slice(0, 8)}...` : part.replace(/-/g, " ")));
  };

  return (
    <header className="rounded-[24px] border border-[#4a1530] bg-[#1f0d16] p-4 text-[#fce4ec] shadow-card">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#ad6883]">
            {getBreadcrumbs().map((crumb, i) => (
              <span key={i} className="flex items-center gap-2">
                {i > 0 && <span className="text-[#7a2550]">/</span>}
                <span>{crumb}</span>
              </span>
            ))}
          </div>
          <h2 className="mt-2 text-[1.35rem] font-semibold tracking-tight text-[#fce4ec]">{getTitle()}</h2>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-green-800 bg-green-950 px-3.5 py-1.5">
          <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs font-medium text-green-300">System Online</span>
        </div>
      </div>
    </header>
  );
}
