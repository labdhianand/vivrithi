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
        <label htmlFor={id} className="block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-dim/90">
          {label}
        </label>
      )}
      <select
        id={id}
        className={cn(
          "w-full appearance-none rounded-xl border border-[#4a1530] bg-[#2d1420] px-3.5 py-2.5 text-sm text-[#fce4ec]",
          "transition-colors duration-200 hover:border-[#7a2550] hover:bg-[#2d1420] focus:border-[#e91e8c] focus:bg-[#2d1420] focus:ring-[#e91e8c]",
          "bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%23ad6883%22%20d%3D%22M6%208L1%203h10z%22%2F%3E%3C%2Fsvg%3E')] bg-[length:12px] bg-[right_12px_center] bg-no-repeat pr-10",
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
