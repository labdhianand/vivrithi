import { cn } from "@/lib/utils";

type Props = {
  children: React.ReactNode;
  tone?: "default" | "success" | "warn" | "danger" | "info" | "neutral";
  className?: string;
  pulse?: boolean;
};

const tones = {
  default: "border-[#e91e8c]/30 bg-[#e91e8c]/15 text-[#ff6bb5]",
  success: "border-green-800 bg-green-950 text-green-300",
  warn: "border-amber-800 bg-amber-950 text-amber-300",
  danger: "border-red-800 bg-red-950 text-red-300",
  info: "border-[#7a2550] bg-[#3d1a2a] text-[#ff6bb5]",
  neutral: "border-[#4a1530] bg-[#1f0d16] text-[#f48fb1]",
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
