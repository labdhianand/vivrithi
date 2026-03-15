import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "gold";
  size?: "sm" | "md" | "lg";
};

const variants = {
  primary:
    "bg-accent text-white font-semibold hover:bg-[#648eff] shadow-glow hover:shadow-[0_22px_46px_rgba(79,124,255,0.28)] active:scale-[0.98]",
  secondary:
    "border border-white/[0.1] bg-white/[0.04] text-slate-bright hover:border-white/[0.16] hover:bg-white/[0.08]",
  ghost:
    "bg-transparent text-slate hover:text-slate-bright hover:bg-white/[0.06]",
  danger:
    "bg-rose-dim text-white hover:bg-rose shadow-glow-rose active:scale-[0.98]",
  gold:
    "bg-gold-dim text-surface font-semibold hover:bg-gold shadow-glow-gold active:scale-[0.98]",
};

const sizes = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({ className, variant = "primary", size = "md", children, ...props }: Props) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium tracking-[0.01em] transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
