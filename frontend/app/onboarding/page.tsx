"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { createCase } from "@/lib/api";
import type { CaseRecord } from "@/lib/types";
import { EntityForm } from "@/components/onboarding/entity-form";
import { LoanForm } from "@/components/onboarding/loan-form";

type Step = 1 | 2;

function isPositiveNumber(value: string) {
  return Number(value) > 0;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [entity, setEntity] = useState<Record<string, string>>({
    company_name: "",
    cin: "",
    pan: "",
    sector: "",
    subsector: "",
    turnover_crore: "",
  });
  const [loan, setLoan] = useState<Record<string, string>>({
    loan_type: "",
    loan_amount_crore: "",
    loan_tenure_months: "",
    proposed_rate_percent: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const entityErrors = useMemo(() => {
    const next: Record<string, string> = {};
    if (!entity.company_name.trim()) next.company_name = "Company name is required.";
    if (entity.cin.trim().length !== 21) next.cin = "CIN must be exactly 21 characters.";
    if (entity.pan.trim().length !== 10) next.pan = "PAN must be exactly 10 characters.";
    if (!entity.sector) next.sector = "Sector is required.";
    if (!isPositiveNumber(entity.turnover_crore)) next.turnover_crore = "Annual turnover must be greater than zero.";
    return next;
  }, [entity]);

  const loanErrors = useMemo(() => {
    const next: Record<string, string> = {};
    if (!loan.loan_type) next.loan_type = "Loan type is required.";
    if (!isPositiveNumber(loan.loan_amount_crore)) next.loan_amount_crore = "Loan amount must be greater than zero.";
    if (!isPositiveNumber(loan.loan_tenure_months)) next.loan_tenure_months = "Tenure must be greater than zero.";
    if (!isPositiveNumber(loan.proposed_rate_percent)) next.proposed_rate_percent = "Interest rate must be greater than zero.";
    return next;
  }, [loan]);

  const canMoveToLoan = Object.keys(entityErrors).length === 0;
  const canSubmit = canMoveToLoan && Object.keys(loanErrors).length === 0;

  return (
    <div className="min-h-screen bg-[#1a0a0f] px-4 py-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6">
          <span className="inline-flex rounded-full border border-[#7a2550] bg-[#3d1a2a] px-3 py-1 text-sm text-[#f48fb1]">
            New Credit Application
          </span>
          <h1 className="mt-4 text-2xl font-bold text-[#fce4ec]">Entity Onboarding</h1>
          <p className="mt-1 text-sm text-[#ad6883]">Enter company and loan details to begin</p>
        </div>

        <div className="mb-6 flex items-center justify-between gap-4">
          <span className="inline-flex rounded-full bg-[#e91e8c] px-3 py-1 text-xs font-medium text-white">
            {step === 1 ? "Step 1 of 2 — Company Details" : "Step 2 of 2 — Loan Details"}
          </span>
          <div className="flex items-center gap-2">
            <span className={`h-3 w-3 rounded-full ${step === 1 ? "bg-[#e91e8c]" : "bg-[#8b2252]"}`} />
            <span className={`h-0.5 w-10 ${step === 2 ? "bg-[#e91e8c]" : "bg-[#4a1530]"}`} />
            <span className={`h-3 w-3 rounded-full ${step === 2 ? "bg-[#e91e8c]" : "bg-[#4a1530]"}`} />
          </div>
        </div>

        <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-8">
          {step === 1 ? (
            <EntityForm
              value={entity}
              errors={entityErrors}
              onChange={setEntity}
              canProceed={canMoveToLoan}
              onNext={() => setStep(2)}
            />
          ) : (
            <LoanForm
              value={loan}
              errors={loanErrors}
              onChange={setLoan}
              canSubmit={canSubmit}
              submitting={submitting}
              onBack={() => setStep(1)}
              onSubmit={async () => {
                try {
                  setSubmitting(true);
                  setError(null);
                  const payload: Record<string, unknown> = { status: "onboarding" };
                  for (const [key, value] of Object.entries({ ...entity, ...loan })) {
                    payload[key] = value === "" ? null : value;
                  }
                  const record = await createCase(payload as Partial<CaseRecord>);
                  router.push(`/cases/${record.id}`);
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed to create case");
                } finally {
                  setSubmitting(false);
                }
              }}
            />
          )}

          {error ? (
            <div className="mt-6 rounded-xl border border-red-800 bg-red-950 px-4 py-3 text-sm text-red-300">{error}</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
