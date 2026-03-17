"use client";

import type { ReactNode } from "react";

interface Props {
  value: Record<string, string>;
  errors: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
  onNext: () => void;
  canProceed: boolean;
}

const sectorOptions = [
  "NBFC",
  "Manufacturing",
  "Infrastructure",
  "Real Estate",
  "Healthcare",
  "Retail",
  "Agri & Food Processing",
  "IT & Technology",
  "Logistics",
  "Energy & Power",
  "Other",
];

function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-[#f48fb1]">{label}</label>
      {children}
      {hint ? <p className="mt-1 text-xs text-[#ad6883]">{hint}</p> : null}
      {error ? <p className="mt-1 text-sm text-red-400">{error}</p> : null}
    </div>
  );
}

const baseInputClass =
  "w-full rounded-lg border bg-[#2d1420] px-3 py-2 text-[#fce4ec] placeholder:text-[#ad6883] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]";

export function EntityForm({ value, errors, onChange, onNext, canProceed }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="space-y-5">
      <div className="grid gap-5 md:grid-cols-2">
        <Field label="Company Name" error={errors.company_name}>
          <input
            value={value.company_name || ""}
            onChange={(event) => setField("company_name", event.target.value)}
            placeholder="Enter company name"
            className={`${baseInputClass} ${errors.company_name ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="CIN" hint="Corporate Identity Number (21 characters)" error={errors.cin}>
          <input
            value={value.cin || ""}
            onChange={(event) => setField("cin", event.target.value.toUpperCase())}
            maxLength={21}
            placeholder="Enter CIN"
            className={`${baseInputClass} uppercase ${errors.cin ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="PAN" hint="Permanent Account Number (10 characters)" error={errors.pan}>
          <input
            value={value.pan || ""}
            onChange={(event) => setField("pan", event.target.value.toUpperCase())}
            maxLength={10}
            placeholder="Enter PAN"
            className={`${baseInputClass} uppercase ${errors.pan ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="Sector" error={errors.sector}>
          <select
            value={value.sector || ""}
            onChange={(event) => setField("sector", event.target.value)}
            className={`${baseInputClass} ${errors.sector ? "border-red-500" : "border-[#4a1530]"}`}
          >
            <option value="">Select sector</option>
            {sectorOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Sub-sector" error={errors.subsector}>
          <input
            value={value.subsector || ""}
            onChange={(event) => setField("subsector", event.target.value)}
            placeholder="Optional"
            className={`${baseInputClass} ${errors.subsector ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="Annual Turnover" error={errors.turnover_crore}>
          <input
            type="number"
            inputMode="decimal"
            value={value.turnover_crore || ""}
            onChange={(event) => setField("turnover_crore", event.target.value)}
            placeholder="in Crores"
            className={`${baseInputClass} ${errors.turnover_crore ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>
      </div>

      <button
        type="button"
        onClick={onNext}
        disabled={!canProceed}
        className="mt-4 w-full rounded-lg bg-[#e91e8c] px-6 py-2 font-medium text-white transition-colors hover:bg-[#c4187a] disabled:cursor-not-allowed disabled:opacity-50"
      >
        Next
      </button>
    </div>
  );
}
