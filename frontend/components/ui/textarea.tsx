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
          "w-full rounded-xl border border-[#4a1530] bg-[#2d1420] px-3.5 py-2.5 text-sm text-[#fce4ec]",
          "placeholder:text-[#ad6883] transition-colors duration-200 resize-none",
          "hover:border-[#7a2550] hover:bg-[#2d1420] focus:border-[#e91e8c] focus:bg-[#2d1420] focus:ring-[#e91e8c]",
          className,
        )}
        rows={4}
        {...props}
      />
    </div>
  );
}
