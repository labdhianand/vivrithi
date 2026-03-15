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
    <div className="min-h-screen bg-[#eef3fb] px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">New Credit Application</h1>
          <p className="mt-2 text-[15px] text-slate-500">
            Capture borrower details and the proposed facility before starting document review.
          </p>
        </div>

        <div className="rounded-[28px] border border-slate-200/80 bg-white/[0.92] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="mb-6">
            <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700">
              {step === 1 ? "Step 1 of 2 - Company Details" : "Step 2 of 2 - Loan Details"}
            </span>
          </div>

          {step === 1 ? (
            <EntityForm value={entity} errors={entityErrors} onChange={setEntity} />
          ) : (
            <LoanForm value={loan} errors={loanErrors} onChange={setLoan} />
          )}

          {error ? (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
          ) : null}

          <div className="mt-8 flex items-center justify-between">
            <button
              type="button"
              onClick={() => (step === 1 ? router.push("/") : setStep(1))}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              Back
            </button>

            {step === 1 ? (
              <button
                type="button"
                disabled={!canMoveToLoan}
                onClick={() => setStep(2)}
                className="rounded-xl bg-[#4f7cff] px-4 py-2 font-medium text-white transition-colors hover:bg-[#3b63d9] disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                disabled={submitting || !canSubmit}
                onClick={async () => {
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
                className="inline-flex items-center gap-2 rounded-xl bg-[#4f7cff] px-4 py-2 font-medium text-white transition-colors hover:bg-[#3b63d9] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                    Creating case...
                  </>
                ) : (
                  "Submit"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
