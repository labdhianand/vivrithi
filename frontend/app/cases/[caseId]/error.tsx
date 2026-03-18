"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function CaseRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <Card glow className="space-y-4">
      <div>
        <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Case Overview</div>
        <h2 className="mt-2 text-2xl font-semibold text-slate-bright">This case page crashed</h2>
        <p className="mt-2 text-sm text-slate-dim">
          {error.message || "An unexpected error occurred while rendering this case."}
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={reset}>
          Retry
        </Button>
        <Link href="/cases">
          <Button type="button" variant="secondary">Back to cases</Button>
        </Link>
      </div>
    </Card>
  );
}
