import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  options?: { value: string; label: string }[];
};

export function Select({ className, label, id, options, children, ...props }: Props) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-xs font-medium uppercase tracking-wider text-slate-dim">
          {label}
        </label>
      )}
      <select
        id={id}
        className={cn(
          "w-full appearance-none rounded-xl border border-white/[0.08] bg-surface-200 px-3.5 py-2.5 text-sm text-slate-bright",
          "transition-all duration-200 hover:border-white/[0.12] focus:border-accent/50 focus:bg-surface-100",
          "bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%2394a3b8%22%20d%3D%22M6%208L1%203h10z%22%2F%3E%3C%2Fsvg%3E')] bg-[length:12px] bg-[right_12px_center] bg-no-repeat pr-10",
          className,
        )}
        {...props}
      >
        {options ? (
          <>
            <option value="">Select...</option>
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </>
        ) : (
          children
        )}
      </select>
    </div>
  );
}
