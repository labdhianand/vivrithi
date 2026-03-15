"use client";

import { useRouter } from "next/navigation";

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#08111f] via-[#0d1830] to-[#12233d] px-4">
      <div className="w-full max-w-4xl rounded-[36px] border border-white/10 bg-slate-950/[0.72] px-8 py-12 text-center shadow-[0_32px_80px_rgba(4,10,26,0.55)] backdrop-blur-xl">
        <div className="mx-auto inline-flex items-center rounded-full border border-white/[0.12] bg-white/[0.05] px-3.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#b6c8f2]">
          AI Credit Intelligence Platform
        </div>
        <h1 className="mt-6 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl">Intelli-Credit</h1>
        <p className="mt-3 text-xl font-medium text-slate-300">AI-Powered Credit Appraisal Engine</p>
        <p className="mx-auto mt-4 max-w-lg text-center text-[15px] leading-7 text-slate-400">
          Transform raw financial documents into comprehensive investment assessment reports in minutes. Built for
          Indian credit analysts.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {[
            "Marker OCR",
            "Firecrawl Research",
            "Gemini AI",
            "Five Cs Scoring",
            "SWOT Analysis",
            "CAM Report",
          ].map((feature) => (
            <span
              key={feature}
              className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-sm font-medium text-[#b6c8f2]"
            >
              {feature}
            </span>
          ))}
        </div>

        <button
          type="button"
          onClick={() => router.push("/onboarding")}
          className="mt-10 inline-flex items-center justify-center rounded-2xl bg-[#4f7cff] px-8 py-4 text-lg font-semibold text-white shadow-[0_20px_44px_rgba(79,124,255,0.28)] transition-all hover:scale-[1.02] hover:bg-[#648eff]"
        >
          Start New Application
        </button>

        <p className="mt-6 text-sm font-medium uppercase tracking-[0.14em] text-slate-500">
          End-to-end appraisal in 4 guided steps
        </p>
      </div>
    </div>
  );
}
