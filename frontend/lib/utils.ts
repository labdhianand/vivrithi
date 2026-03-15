import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(value: number | string | null | undefined, unit = "Cr") {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  return `Rs. ${value} ${unit}`;
}

export function formatPercent(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  return `${value}%`;
}

export const STAGES = [
  { key: "onboarding", label: "Onboarding", href: "/onboarding" },
  { key: "ingestion", label: "Ingestion", href: "/cases" },
  { key: "extraction", label: "Extraction", href: "/cases" },
  { key: "analysis", label: "Analysis", href: "/cases" },
  { key: "report", label: "Report", href: "/cases" },
];

export const DOCUMENT_CATEGORIES = [
  "ALM",
  "Shareholding_Pattern",
  "Borrowing_Profile",
  "Annual_Report",
  "Portfolio_Performance",
] as const;
