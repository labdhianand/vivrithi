"use client";

import { useRouter } from "next/navigation";

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#1a0a0f] via-[#241019] to-[#2d1420] px-4 py-8">
      <div className="w-full max-w-4xl rounded-[36px] border border-[#4a1530] bg-[#1f0d16]/90 px-8 py-12 text-center shadow-[0_32px_80px_rgba(26,8,16,0.55)] backdrop-blur-xl">
        <div className="mx-auto inline-flex items-center rounded-full border border-[#7a2550] bg-[#3d1a2a] px-3.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#f48fb1]">
          AI Credit Intelligence Platform
        </div>
        <h1 className="mt-6 text-4xl font-semibold tracking-[-0.05em] text-[#fce4ec] sm:text-5xl">Intelli-Credit</h1>
        <p className="mt-3 text-xl font-medium text-[#f48fb1]">AI-Powered Credit Appraisal Engine</p>
        <p className="mx-auto mt-4 max-w-lg text-center text-[15px] leading-7 text-[#ad6883]">
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
              className="rounded-full border border-[#7a2550] bg-[#3d1a2a] px-3 py-1 text-sm font-medium text-[#f48fb1]"
            >
              {feature}
            </span>
          ))}
        </div>

        <button
          type="button"
          onClick={() => router.push("/onboarding")}
          className="mt-10 inline-flex items-center justify-center rounded-2xl bg-[#e91e8c] px-8 py-4 text-lg font-semibold text-white shadow-[0_20px_44px_rgba(233,30,140,0.28)] transition-all hover:scale-[1.02] hover:bg-[#c4187a]"
        >
          Start New Application
        </button>

        <p className="mt-6 text-sm font-medium uppercase tracking-[0.14em] text-[#ad6883]">
          End-to-end appraisal in 4 guided steps
        </p>
      </div>
    </div>
  );
}
