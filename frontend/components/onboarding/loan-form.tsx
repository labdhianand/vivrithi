"use client";

import type { ReactNode } from "react";

interface Props {
  value: Record<string, string>;
  errors: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
  onBack: () => void;
  onSubmit: () => Promise<void>;
  canSubmit: boolean;
  submitting: boolean;
}

const loanTypeOptions = [
  "Term Loan",
  "Working Capital",
  "Cash Credit",
  "Letter of Credit",
  "Bank Guarantee",
  "ECLGS",
  "Other",
];

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-[#f48fb1]">{label}</label>
      {children}
      {error ? <p className="mt-1 text-sm text-red-400">{error}</p> : null}
    </div>
  );
}

const baseInputClass =
  "w-full rounded-lg border bg-[#2d1420] px-3 py-2 text-[#fce4ec] placeholder:text-[#ad6883] focus:border-[#e91e8c] focus:outline-none focus:ring-2 focus:ring-[#e91e8c]";

export function LoanForm({ value, errors, onChange, onBack, onSubmit, canSubmit, submitting }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="space-y-5">
      <div className="grid gap-5 md:grid-cols-2">
        <Field label="Loan Type" error={errors.loan_type}>
          <select
            value={value.loan_type || ""}
            onChange={(event) => setField("loan_type", event.target.value)}
            className={`${baseInputClass} ${errors.loan_type ? "border-red-500" : "border-[#4a1530]"}`}
          >
            <option value="">Select loan type</option>
            {loanTypeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Loan Amount" error={errors.loan_amount_crore}>
          <input
            type="number"
            inputMode="decimal"
            value={value.loan_amount_crore || ""}
            onChange={(event) => setField("loan_amount_crore", event.target.value)}
            placeholder="in Crores"
            className={`${baseInputClass} ${errors.loan_amount_crore ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="Tenure" error={errors.loan_tenure_months}>
          <input
            type="number"
            inputMode="numeric"
            value={value.loan_tenure_months || ""}
            onChange={(event) => setField("loan_tenure_months", event.target.value)}
            placeholder="in months"
            className={`${baseInputClass} ${errors.loan_tenure_months ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>

        <Field label="Interest Rate" error={errors.proposed_rate_percent}>
          <input
            type="number"
            inputMode="decimal"
            value={value.proposed_rate_percent || ""}
            onChange={(event) => setField("proposed_rate_percent", event.target.value)}
            placeholder="% p.a."
            className={`${baseInputClass} ${errors.proposed_rate_percent ? "border-red-500" : "border-[#4a1530]"}`}
          />
        </Field>
      </div>

      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-[#7a2550] bg-[#3d1a2a] px-6 py-2 font-medium text-[#f48fb1] transition-colors hover:bg-[#4a1530]"
        >
          Back
        </button>
        <button
          type="button"
          disabled={submitting || !canSubmit}
          onClick={onSubmit}
          className="inline-flex items-center gap-2 rounded-lg bg-[#e91e8c] px-6 py-2 font-medium text-white transition-colors hover:bg-[#c4187a] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Creating case...
            </>
          ) : (
            "Create Case"
          )}
        </button>
      </div>
    </div>
  );
}
