import type { Metadata } from "next";
import { Instrument_Serif, Sora } from "next/font/google";

import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { StageStepper } from "@/components/layout/stage-stepper";

import "./globals.css";

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-instrument-serif",
  weight: "400",
});

export const metadata: Metadata = {
  title: "Intelli-Credit | AI-Powered Credit Decisioning",
  description: "Next-gen corporate credit appraisal engine for Indian enterprise lending.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sora.variable} ${instrumentSerif.variable}`}>
      <body className="noise">
        <div className="mx-auto flex max-w-[1640px] gap-5 px-5 py-5">
          <Sidebar />
          <main className="flex-1 space-y-5">
            <Header />
            <StageStepper />
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
