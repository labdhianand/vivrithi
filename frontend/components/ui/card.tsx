import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type CardProps = PropsWithChildren<HTMLAttributes<HTMLDivElement>> & {
  glow?: boolean;
};

export function Card({ className, glow, children, ...props }: CardProps) {
  return (
    <div className={cn(glow ? "panel-glow" : "panel", "p-5", className)} {...props}>
      {children}
    </div>
  );
}
