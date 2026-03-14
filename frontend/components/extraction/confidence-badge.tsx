import { Badge } from "@/components/ui/badge";

export function ConfidenceBadge({ confidence }: { confidence?: string | null }) {
  const numeric = confidence ? Number(confidence) : 0;
  const percent = Math.round(numeric * 100);

  if (numeric >= 0.8) {
    return <Badge tone="success">High {percent}%</Badge>;
  }
  if (numeric >= 0.5) {
    return <Badge tone="warn">Med {percent}%</Badge>;
  }
  return <Badge tone="danger">Low {percent}%</Badge>;
}
