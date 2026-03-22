"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { listCases } from "@/lib/api";
import type { CaseRecord } from "@/lib/types";

type MetricCardProps = {
  icon: ReactNode;
  value: string;
  label: string;
};

type QuickActionProps = {
  icon: ReactNode;
  title: string;
  subtitle: string;
  onClick?: () => void;
  primary?: boolean;
};

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  onboarding: { label: "New", className: "bg-[#3d1a2a] text-[#ad6883]" },
  documents_uploaded: { label: "Uploaded", className: "bg-amber-950 text-amber-300" },
  extracting: { label: "In Progress", className: "bg-[#3d1a2a] text-[#f48fb1]" },
  extracted: { label: "Extracted", className: "bg-blue-950 text-blue-300" },
  analyzing: { label: "In Progress", className: "bg-[#3d1a2a] text-[#f48fb1]" },
  report_ready: { label: "Report Ready", className: "bg-green-950 text-green-300" },
};

function formatStatus(status: string) {
  return STATUS_BADGES[status]?.label || status.replace(/_/g, " ");
}

function formatLoanAmount(value: string | null | undefined) {
  if (!value) {
    return "--";
  }
  return `${value} Cr`;
}

function formatTimeAgo(value: string) {
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) {
    return "just now";
  }

  const diffMs = Date.now() - timestamp;
  const diffMinutes = Math.max(1, Math.floor(diffMs / 60000));

  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) {
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
  }

  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths} mo ago`;
}

function MetricCard({ icon, value, label }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-3xl font-bold text-[#fce4ec]">{value}</div>
          <div className="mt-1 text-sm text-[#ad6883]">{label}</div>
        </div>
        <div className="rounded-lg bg-[#3d1a2a] p-2 text-[#e91e8c]">{icon}</div>
      </div>
    </div>
  );
}

function QuickAction({ icon, title, subtitle, onClick, primary }: QuickActionProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-xl p-4 text-left transition-colors ${
        primary
          ? "bg-[#e91e8c] text-white hover:bg-[#c4187a]"
          : "border border-[#7a2550] bg-[#3d1a2a] text-[#f48fb1] hover:bg-[#4a1530]"
      } ${onClick ? "" : "cursor-default"}`}
    >
      <div className="flex items-start gap-3">
        <div className={primary ? "text-white" : "text-[#f48fb1]"}>{icon}</div>
        <div>
          <div className="font-semibold">{title}</div>
          <div className={`mt-1 text-sm ${primary ? "text-[#fde6f0]" : "text-[#ad6883]"}`}>{subtitle}</div>
        </div>
      </div>
    </button>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCases()
      .then(setCases)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  const recentCases = cases.slice(0, 5);
  const reportsReady = cases.filter((item) => item.status === "report_ready").length;
  const inProgress = cases.filter((item) => !["report_ready", "onboarding"].includes(item.status)).length;

  return (
    <div className="min-h-screen rounded-[28px] bg-[#1a0a0f] p-4 sm:p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        {error ? (
          <div className="rounded-xl border border-red-900 bg-red-950 px-4 py-3 text-sm text-red-300">{error}</div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-4">
          <MetricCard
            value={String(cases.length)}
            label="Total Cases"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M4 7.5A2.5 2.5 0 0 1 6.5 5h11A2.5 2.5 0 0 1 20 7.5v9A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5v-9Z" stroke="currentColor" strokeWidth="1.8" />
                <path d="M9 5V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            }
          />
          <MetricCard
            value={String(reportsReady)}
            label="Reports Ready"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" />
                <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.8" />
                <path d="m9 14 2 2 4-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            }
          />
          <MetricCard
            value={String(inProgress)}
            label="In Progress"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.8" />
                <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            }
          />
          <MetricCard
            value="< 10 min"
            label="Avg Processing Time"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M13 2 5 13h5l-1 9 8-11h-5l1-9Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
              </svg>
            }
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_360px]">
          <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold text-[#fce4ec]">Recent Cases</h1>
                <p className="mt-1 text-sm text-[#ad6883]">Latest credit applications</p>
              </div>
              {loading ? <span className="text-sm text-[#ad6883]">Loading...</span> : null}
            </div>

            <div className="mt-6 overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-[#4a1530] text-[#ad6883]">
                    <th className="pb-3 font-medium">Company</th>
                    <th className="pb-3 font-medium">Sector</th>
                    <th className="pb-3 font-medium">Loan Amount</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recentCases.map((item) => (
                    <tr key={item.id} className="border-b border-[#4a1530]/60 last:border-b-0">
                      <td className="py-4 pr-4 font-medium text-[#fce4ec]">{item.company_name || "Untitled Case"}</td>
                      <td className="py-4 pr-4 text-[#ad6883]">{item.sector || "--"}</td>
                      <td className="py-4 pr-4 text-[#fce4ec]">{formatLoanAmount(item.loan_amount_crore)}</td>
                      <td className="py-4 pr-4">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                            STATUS_BADGES[item.status]?.className || "bg-[#3d1a2a] text-[#f48fb1]"
                          }`}
                        >
                          {formatStatus(item.status)}
                        </span>
                      </td>
                      <td className="py-4 text-right">
                        <Link href={`/cases/${item.id}`} className="font-medium text-[#f48fb1] transition-colors hover:text-[#ff6bb5]">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {!loading && recentCases.length === 0 ? (
              <div className="mt-6 rounded-xl border border-dashed border-[#4a1530] px-4 py-10 text-center text-[#ad6883]">
                No cases yet. Create your first case.
              </div>
            ) : null}
          </div>

          <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6">
            <h2 className="text-xl font-semibold text-[#fce4ec]">Quick Actions</h2>
            <div className="mt-6 space-y-4">
              <QuickAction
                primary
                title="New Credit Application"
                subtitle="Start a new case"
                onClick={() => router.push("/onboarding")}
                icon={
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M10 4v12M4 10h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                }
              />
              <QuickAction
                title="View All Cases"
                subtitle="Browse case pipeline"
                onClick={() => router.push("/cases")}
                icon={
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M4 5h12M4 10h12M4 15h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                }
              />
              <QuickAction
                title="Documentation"
                subtitle="View user guide"
                icon={
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2h7A1.5 1.5 0 0 1 16 3.5v13A1.5 1.5 0 0 1 14.5 18h-7A2.5 2.5 0 0 0 5 15.5v-11Z" stroke="currentColor" strokeWidth="1.8" />
                    <path d="M7 5h6M7 8h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                }
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[#4a1530] bg-[#1f0d16] p-6">
          <h2 className="text-xl font-semibold text-[#fce4ec]">Recent Activity</h2>
          <div className="mt-5 space-y-3">
            {recentCases.map((item) => (
              <div key={`${item.id}-activity`} className="flex items-center gap-3 rounded-lg bg-[#16080d] px-4 py-3 text-sm text-[#fce4ec]">
                <span className="h-2.5 w-2.5 rounded-full bg-[#e91e8c]" />
                <span className="truncate">
                  {item.company_name || "Untitled Case"} - {formatStatus(item.status)} - {formatTimeAgo(item.updated_at || item.created_at)}
                </span>
              </div>
            ))}

            {!loading && recentCases.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[#4a1530] px-4 py-8 text-center text-sm text-[#ad6883]">
                No recent activity yet.
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
