import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type Props = PropsWithChildren<ButtonHTMLAttributes<HTMLButtonElement>> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "gold";
  size?: "sm" | "md" | "lg";
};

const variants = {
  primary:
    "rounded-lg bg-accent text-[#fce4ec] font-medium hover:bg-accent-dim shadow-glow active:scale-[0.98]",
  secondary:
    "rounded-lg border border-[#7a2550] bg-[#3d1a2a] text-[#f48fb1] hover:bg-[#4a1530]",
  ghost:
    "rounded-lg bg-transparent text-slate hover:bg-[#3d1a2a] hover:text-slate-bright",
  danger:
    "rounded-lg bg-red-600 text-[#fce4ec] hover:bg-red-700 shadow-glow-rose active:scale-[0.98]",
  gold:
    "rounded-lg bg-amber-600 text-[#fce4ec] font-medium hover:bg-amber-500 shadow-glow-gold active:scale-[0.98]",
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
        "inline-flex items-center justify-center gap-2 font-medium tracking-[0.01em] transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-40",
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
