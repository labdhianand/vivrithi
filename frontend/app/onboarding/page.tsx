"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createCase } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EntityForm } from "@/components/onboarding/entity-form";
import { LoanForm } from "@/components/onboarding/loan-form";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [entity, setEntity] = useState<Record<string, string>>({
    company_name: "",
    cin: "",
    pan: "",
    sector: "",
    subsector: "",
    turnover_crore: "",
    incorporation_date: "",
    registered_office: "",
  });
  const [loan, setLoan] = useState<Record<string, string>>({
    loan_type: "",
    loan_amount_crore: "",
    loan_tenure_months: "",
    proposed_rate_percent: "",
    loan_purpose: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canProceed = entity.company_name.trim().length > 0;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Step indicator */}
      <div className="animate-slide-up flex items-center justify-center gap-3">
        <button
          onClick={() => setStep(1)}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium uppercase tracking-wider transition-all duration-200 ${
            step === 1
              ? "bg-accent/15 text-accent-glow border border-accent/20"
              : "text-slate-dim hover:text-slate-bright hover:bg-white/[0.04]"
          }`}
        >
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent/20 text-[10px] font-bold text-accent-glow">
            1
          </span>
          Entity
        </button>
        <div className="h-px w-8 bg-white/[0.08]" />
        <button
          onClick={() => canProceed && setStep(2)}
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium uppercase tracking-wider transition-all duration-200 ${
            step === 2
              ? "bg-accent/15 text-accent-glow border border-accent/20"
              : "text-slate-dim hover:text-slate-bright hover:bg-white/[0.04]"
          } ${!canProceed ? "opacity-40 cursor-not-allowed" : ""}`}
        >
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/[0.06] text-[10px] font-bold text-slate-dim">
            2
          </span>
          Loan
        </button>
      </div>

      {/* Step 1: Entity */}
      {step === 1 && (
        <div className="animate-slide-up stagger-1">
          <Card glow>
            <div className="mb-6">
              <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                Stage 1 of 2
              </div>
              <h2 className="text-gradient mt-2 font-serif text-3xl">Entity Onboarding</h2>
              <p className="mt-1 text-sm text-slate-dim">
                Enter the borrower company details to begin the underwriting process.
              </p>
            </div>
            <EntityForm value={entity} onChange={setEntity} />
            <div className="mt-6 flex justify-end">
              <Button disabled={!canProceed} onClick={() => setStep(2)}>
                Continue to loan details
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Step 2: Loan */}
      {step === 2 && (
        <div className="animate-slide-up stagger-1">
          <Card glow>
            <div className="mb-6">
              <div className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">
                Stage 2 of 2
              </div>
              <h2 className="text-gradient mt-2 font-serif text-3xl">Borrowing Proposal</h2>
              <p className="mt-1 text-sm text-slate-dim">
                Specify the loan parameters for {entity.company_name || "this entity"}.
              </p>
            </div>
            <LoanForm value={loan} onChange={setLoan} />
            <div className="mt-6 flex items-center justify-between">
              <Button variant="ghost" onClick={() => setStep(1)}>
                Back
              </Button>
              <div className="flex items-center gap-4">
                {error && <span className="text-sm text-rose-glow">{error}</span>}
                <Button
                  disabled={submitting || !canProceed}
                  onClick={async () => {
                    try {
                      setSubmitting(true);
                      setError(null);
                      // Strip empty strings so Pydantic gets null instead of ""
                      const payload: Record<string, unknown> = { status: "onboarding" };
                      for (const [k, v] of Object.entries({ ...entity, ...loan })) {
                        payload[k] = v === "" ? null : v;
                      }
                      const record = await createCase(payload as any);
                      router.push(`/cases/${record.id}`);
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Failed to create case");
                    } finally {
                      setSubmitting(false);
                    }
                  }}
                >
                  {submitting ? "Creating..." : "Create case"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
