"use client";

import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
}

const sectorOptions = [
  { value: "NBFC", label: "NBFC" },
  { value: "Banking", label: "Banking" },
  { value: "Manufacturing", label: "Manufacturing" },
  { value: "IT", label: "IT / Software" },
  { value: "Infrastructure", label: "Infrastructure" },
  { value: "Real Estate", label: "Real Estate" },
  { value: "Healthcare", label: "Healthcare" },
  { value: "Energy", label: "Energy" },
  { value: "Other", label: "Other" },
];

export function EntityForm({ value, onChange }: Props) {
  const setField = (key: string, nextValue: string) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="animate-fade-in stagger-1">
          <Input
            label="Company name"
            placeholder="e.g. Acme Corp Pvt Ltd"
            value={value.company_name || ""}
            onChange={(event) => setField("company_name", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-2">
          <Input
            label="CIN"
            placeholder="Corporate Identity Number"
            value={value.cin || ""}
            onChange={(event) => setField("cin", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-3">
          <Input
            label="PAN"
            placeholder="Permanent Account Number"
            value={value.pan || ""}
            onChange={(event) => setField("pan", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-3">
          <Select
            label="Sector"
            options={sectorOptions}
            value={value.sector || ""}
            onChange={(event) => setField("sector", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-4">
          <Input
            label="Subsector"
            placeholder="e.g. Micro-lending"
            value={value.subsector || ""}
            onChange={(event) => setField("subsector", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-4">
          <Input
            label="Turnover (crore)"
            placeholder="Annual turnover in crore"
            value={value.turnover_crore || ""}
            onChange={(event) => setField("turnover_crore", event.target.value)}
          />
        </div>
        <div className="animate-fade-in stagger-5">
          <Input
            label="Incorporation date"
            type="date"
            value={value.incorporation_date || ""}
            onChange={(event) => setField("incorporation_date", event.target.value)}
          />
        </div>
      </div>
      <div className="animate-fade-in stagger-6">
        <Textarea
          label="Registered office"
          rows={3}
          placeholder="Full registered office address"
          value={value.registered_office || ""}
          onChange={(event) => setField("registered_office", event.target.value)}
        />
      </div>
    </div>
  );
}
