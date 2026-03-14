"use client";

import type { MouseEvent } from "react";

interface Box {
  id: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export function BBoxOverlay({
  boxes,
  activeId,
  onSelect,
}: {
  boxes: Box[];
  activeId?: string;
  onSelect?: (id: string) => void;
}) {
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
      {boxes.map((box) => {
        const isActive = activeId === box.id;
        const handleClick = (event: MouseEvent<SVGRectElement>) => {
          event.stopPropagation();
          onSelect?.(box.id);
        };
        return (
          <rect
            key={box.id}
            x={box.x1 * 100}
            y={box.y1 * 100}
            width={(box.x2 - box.x1) * 100}
            height={(box.y2 - box.y1) * 100}
            rx="0.6"
            fill={isActive ? "rgba(6,182,212,0.18)" : "rgba(34,211,238,0.06)"}
            stroke={isActive ? "#22d3ee" : "rgba(34,211,238,0.45)"}
            strokeWidth={isActive ? 0.5 : 0.3}
            className="cursor-pointer transition-all duration-200"
            onClick={handleClick}
          />
        );
      })}
    </svg>
  );
}
