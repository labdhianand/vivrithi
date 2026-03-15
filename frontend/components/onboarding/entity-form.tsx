"use client";

interface Props {
  value: Record<string, string>;
  errors: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
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
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-semibold text-slate-800">{label}</label>
      {children}
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
      {error ? <p className="mt-1 text-sm text-red-500">{error}</p> : null}
    </div>
  );
}

export function EntityForm({ value, errors, onChange }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Field label="Company Name" error={errors.company_name}>
        <input
          value={value.company_name || ""}
          onChange={(event) => setField("company_name", event.target.value)}
          placeholder="Enter company name"
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field
        label="CIN"
        hint="Corporate Identity Number (21 characters)"
        error={errors.cin}
      >
        <input
          value={value.cin || ""}
          onChange={(event) => setField("cin", event.target.value.toUpperCase())}
          maxLength={21}
          placeholder="Enter CIN"
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 uppercase text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field
        label="PAN"
        hint="Permanent Account Number (10 characters)"
        error={errors.pan}
      >
        <input
          value={value.pan || ""}
          onChange={(event) => setField("pan", event.target.value.toUpperCase())}
          maxLength={10}
          placeholder="Enter PAN"
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 uppercase text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field label="Sector" error={errors.sector}>
        <select
          value={value.sector || ""}
          onChange={(event) => setField("sector", event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
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
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>

      <Field label="Annual Turnover" error={errors.turnover_crore}>
        <input
          type="number"
          inputMode="decimal"
          value={value.turnover_crore || ""}
          onChange={(event) => setField("turnover_crore", event.target.value)}
          placeholder="in Crores"
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-800 shadow-sm shadow-slate-100/50 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-[#4f7cff]"
        />
      </Field>
    </div>
  );
}
