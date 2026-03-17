import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type CardProps = PropsWithChildren<HTMLAttributes<HTMLDivElement>> & {
  glow?: boolean;
};

export function Card({ className, glow, children, ...props }: CardProps) {
  return (
    <div className={cn(glow ? "panel-glow" : "panel", "rounded-xl border border-[#4a1530] bg-[#1f0d16] p-5 md:p-6", className)} {...props}>
      {children}
    </div>
  );
}
