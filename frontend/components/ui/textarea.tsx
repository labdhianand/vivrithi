import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: string;
};

export function Textarea({ className, label, id, ...props }: Props) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-dim/90">
          {label}
        </label>
      )}
      <textarea
        id={id}
        className={cn(
          "w-full rounded-xl border border-white/[0.09] bg-white/[0.04] px-3.5 py-2.5 text-sm text-slate-bright",
          "placeholder:text-slate-dim/70 transition-all duration-200 resize-none",
          "hover:border-white/[0.14] hover:bg-white/[0.05] focus:border-accent/50 focus:bg-surface-50",
          className,
        )}
        rows={4}
        {...props}
      />
    </div>
  );
}
