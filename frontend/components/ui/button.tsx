import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "gold";
  size?: "sm" | "md" | "lg";
};

const variants = {
  primary:
    "bg-accent text-surface font-semibold hover:bg-accent-glow shadow-glow hover:shadow-[0_0_48px_rgba(6,182,212,0.3)] active:scale-[0.97]",
  secondary:
    "bg-surface-300 text-slate-bright border border-white/[0.08] hover:bg-surface-400 hover:border-white/[0.12]",
  ghost:
    "bg-transparent text-slate hover:text-slate-bright hover:bg-white/[0.04]",
  danger:
    "bg-rose-dim text-white hover:bg-rose shadow-glow-rose active:scale-[0.97]",
  gold:
    "bg-gold-dim text-surface font-semibold hover:bg-gold shadow-glow-gold active:scale-[0.97]",
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
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40",
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
