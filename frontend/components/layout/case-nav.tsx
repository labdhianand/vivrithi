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
    <div className="flex flex-wrap gap-1.5 rounded-[20px] border border-[#4a1530] bg-[#1f0d16] p-2">
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
                ? "border border-[#7a2550] bg-[#3d1a2a] text-[#e91e8c]"
                : "text-[#ad6883] hover:bg-[#2d1420] hover:text-[#f48fb1]",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
