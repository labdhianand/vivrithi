import { cn } from "@/lib/utils";

type Props = {
  children: React.ReactNode;
  tone?: "default" | "success" | "warn" | "danger" | "info" | "neutral";
  className?: string;
  pulse?: boolean;
};

const tones = {
  default: "border-accent/20 bg-accent/[0.12] text-accent-glow",
  success: "border-emerald/20 bg-emerald/[0.12] text-emerald-glow",
  warn: "border-gold/20 bg-gold/[0.12] text-gold-glow",
  danger: "border-rose/20 bg-rose/[0.12] text-rose-glow",
  info: "border-blue-400/20 bg-blue-400/[0.12] text-blue-200",
  neutral: "border-white/[0.1] bg-white/[0.05] text-slate",
};

export function Badge({ children, tone = "default", className, pulse }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
        tones[tone],
        pulse && "animate-pulse",
        className,
      )}
    >
      {pulse && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
