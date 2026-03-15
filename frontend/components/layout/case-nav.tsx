"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const tabs = [
  { key: "overview", label: "Overview", suffix: "" },
  { key: "upload", label: "Upload", suffix: "/upload" },
  { key: "classify", label: "Classify", suffix: "/classify" },
  { key: "extraction", label: "Extraction", suffix: "/extraction" },
  { key: "schema", label: "Schema", suffix: "/schema" },
  { key: "analysis", label: "Analysis", suffix: "/analysis" },
  { key: "report", label: "Report", suffix: "/report" },
];

export function CaseNav({ caseId }: { caseId: string }) {
  const pathname = usePathname();

  return (
    <div className="panel flex flex-wrap gap-1.5 p-2">
      {tabs.map((tab) => {
        const href = `/cases/${caseId}${tab.suffix}`;
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={tab.key}
            href={href}
            className={cn(
              "rounded-xl px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.12em] transition-all duration-200",
              active
                ? "border border-white/[0.14] bg-white/[0.08] text-slate-bright"
                : "text-slate-dim hover:bg-white/[0.05] hover:text-slate-bright",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
