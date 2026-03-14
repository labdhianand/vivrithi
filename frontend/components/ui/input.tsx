import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export function Input({ className, label, id, ...props }: Props) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-xs font-medium uppercase tracking-wider text-slate-dim">
          {label}
        </label>
      )}
      <input
        id={id}
        className={cn(
          "w-full rounded-xl border border-white/[0.08] bg-surface-200 px-3.5 py-2.5 text-sm text-slate-bright",
          "placeholder:text-slate-dim/60 transition-all duration-200",
          "hover:border-white/[0.12] focus:border-accent/50 focus:bg-surface-100",
          className,
        )}
        {...props}
      />
    </div>
  );
}
