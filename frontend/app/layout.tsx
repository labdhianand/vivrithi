import type { Metadata } from "next";
import { Fraunces, Manrope } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";

import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
});

export const metadata: Metadata = {
  title: "Intelli-Credit | AI-Powered Credit Decisioning",
  description: "Next-gen corporate credit appraisal engine for Indian enterprise lending.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${manrope.variable} ${fraunces.variable}`}>
      <body className="noise">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
