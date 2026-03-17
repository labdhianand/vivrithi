import { Badge } from "@/components/ui/badge";

const icons = {
  positive: (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22" />
    </svg>
  ),
  negative: (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6 9 12.75l4.286-4.286a11.948 11.948 0 0 1 5.814 5.518l2.74 1.22" />
    </svg>
  ),
  neutral: (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  ),
};

export function SentimentBadge({ value }: { value?: string | null }) {
  if (value === "positive") {
    return (
      <Badge tone="success">
        <span className="flex items-center gap-1">
          {icons.positive}
          Positive
        </span>
      </Badge>
    );
  }
  if (value === "negative") {
    return (
      <Badge tone="danger">
        <span className="flex items-center gap-1">
          {icons.negative}
          Negative
        </span>
      </Badge>
    );
  }
  return (
    <Badge tone="neutral" className="border-[#7a2550] bg-[#3d1a2a] text-[#f48fb1]">
      <span className="flex items-center gap-1">
        {icons.neutral}
        Neutral
      </span>
    </Badge>
  );
}
