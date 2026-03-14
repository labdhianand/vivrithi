import { cn } from "@/lib/utils";

type Props = {
  children: React.ReactNode;
  tone?: "default" | "success" | "warn" | "danger" | "info" | "neutral";
  className?: string;
  pulse?: boolean;
};

const tones = {
  default: "bg-accent/15 text-accent-glow border-accent/20",
  success: "bg-emerald/15 text-emerald-glow border-emerald/20",
  warn: "bg-gold/15 text-gold-glow border-gold/20",
  danger: "bg-rose/15 text-rose-glow border-rose/20",
  info: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  neutral: "bg-white/[0.06] text-slate border-white/[0.08]",
};

export function Badge({ children, tone = "default", className, pulse }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider",
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
