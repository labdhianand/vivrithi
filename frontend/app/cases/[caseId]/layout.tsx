import type { ReactNode } from "react";

import { CaseNav } from "@/components/layout/case-nav";

export default function CaseLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: { caseId: string };
}) {
  return (
    <div className="space-y-6 rounded-[28px] border border-[#4a1530] bg-[#1a0a0f]/45 p-4 sm:p-5">
      <div className="animate-slide-up">
        <CaseNav caseId={params.caseId} />
      </div>
      <div className="animate-fade-in stagger-2">{children}</div>
    </div>
  );
}
