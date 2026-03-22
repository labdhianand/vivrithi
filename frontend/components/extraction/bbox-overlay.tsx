"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

interface Box {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export function BBoxOverlay({
  boxes,
  selectedBoxId,
  selectedBox,
  pulseSelected = false,
  onSelect,
}: {
  boxes: Box[];
  selectedBoxId?: string;
  selectedBox?: Box | null;
  pulseSelected?: boolean;
  onSelect?: (id: string) => void;
}) {
  const selectedRef = useRef<HTMLButtonElement | HTMLDivElement | null>(null);

  useEffect(() => {
    if (!selectedRef.current) {
      return;
    }
    selectedRef.current.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
  }, [selectedBoxId, selectedBox?.id]);

  const shouldRenderStandaloneSelected =
    selectedBox && !boxes.some((box) => box.id === selectedBox.id);

  return (
    <div className="absolute inset-0">
      {boxes.map((box) => {
        const isSelected = selectedBoxId === box.id;
        return (
          <button
            key={box.id}
            ref={isSelected ? (node) => { selectedRef.current = node; } : undefined}
            type="button"
            className={cn(
              "absolute cursor-pointer rounded-[6px] border transition-all duration-200",
              isSelected
                ? "border-[#e91e8c] bg-[#e91e8c]/20"
                : "border-[#4a1530] bg-transparent hover:border-[#7a2550]",
              isSelected && pulseSelected && "animate-pulse",
            )}
            style={{
              left: `${box.x * 100}%`,
              top: `${box.y * 100}%`,
              width: `${box.width * 100}%`,
              height: `${box.height * 100}%`,
            }}
            onClick={(event) => {
              event.stopPropagation();
              onSelect?.(box.id);
            }}
          />
        );
      })}

      {shouldRenderStandaloneSelected ? (
        <div
          ref={(node) => {
            selectedRef.current = node;
          }}
          className={cn(
            "absolute rounded-[6px] border-2 border-[#e91e8c] bg-[#e91e8c]/20",
            pulseSelected && "animate-pulse",
          )}
          style={{
            left: `${selectedBox.x * 100}%`,
            top: `${selectedBox.y * 100}%`,
            width: `${selectedBox.width * 100}%`,
            height: `${selectedBox.height * 100}%`,
          }}
        />
      ) : null}
    </div>
  );
}
