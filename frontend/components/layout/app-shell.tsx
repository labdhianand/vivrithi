"use client";

import { usePathname } from "next/navigation";

import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { StageStepper } from "@/components/layout/stage-stepper";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const isFullscreenPage = pathname === "/" || pathname === "/onboarding";

  if (isFullscreenPage) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="mx-auto flex max-w-[1640px] gap-5 px-5 py-5">
      <Sidebar />
      <main className="flex-1 space-y-5">
        <Header />
        <StageStepper />
        {children}
      </main>
    </div>
  );
}
