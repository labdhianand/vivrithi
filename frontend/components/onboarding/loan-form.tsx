"use client";

import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
}

const loanTypeOptions = [
  { value: "term_loan", label: "Term Loan" },
  { value: "working_capital", label: "Working Capital" },
  { value: "project_finance", label: "Project Finance" },
  { value: "ncd", label: "Non-Convertible Debenture" },
  { value: "line_of_credit", label: "Line of Credit" },
  { value: "other", label: "Other" },
];

export function LoanForm({ value, onChange }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="animate-fade-in stagger-1">
          <Select
            label="Loan type"
            options={loanTypeOptions}
            value={value.loan_type || ""}
            onChange={(event) => setField("loan_type", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-2">
          <Input
            label="Amount (crore)"
            placeholder="Requested loan amount"
            value={value.loan_amount_crore || ""}
            onChange={(event) => setField("loan_amount_crore", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-3">
          <Input
            label="Tenure (months)"
            placeholder="Loan tenure in months"
            value={value.loan_tenure_months || ""}
            onChange={(event) => setField("loan_tenure_months", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-4">
          <Input
            label="Proposed rate (%)"
            placeholder="Annual interest rate"
            value={value.proposed_rate_percent || ""}
            onChange={(event) => setField("proposed_rate_percent", event.target.value)}
          />
        </div>
      </div>
      <div className="animate-fade-in stagger-5">
        <Textarea
          label="Loan purpose"
          rows={3}
          placeholder="Describe the intended use of funds"
          value={value.loan_purpose || ""}
          onChange={(event) => setField("loan_purpose", event.target.value)}
        />
      </div>
    </div>
  );
}
