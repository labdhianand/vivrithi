"use client";

interface Props {
  value: Record<string, string>;
  errors: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
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
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-semibold text-slate-800">{label}</label>
      {children}
      {error ? <p className="mt-1 text-sm text-red-500">{error}</p> : null}
    </div>
  );
}

export function LoanForm({ value, errors, onChange }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Field label="Loan Type" error={errors.loan_type}>
        <select
          value={value.loan_type || ""}
          onChange={(event) => setField("loan_type", event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
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
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field label="Tenure" error={errors.loan_tenure_months}>
        <input
          type="number"
          inputMode="numeric"
          value={value.loan_tenure_months || ""}
          onChange={(event) => setField("loan_tenure_months", event.target.value)}
          placeholder="in months"
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field label="Interest Rate" error={errors.proposed_rate_percent}>
        <input
          type="number"
          inputMode="decimal"
          value={value.proposed_rate_percent || ""}
          onChange={(event) => setField("proposed_rate_percent", event.target.value)}
          placeholder="% p.a."
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>
    </div>
  );
}
