"use client";

import { useState } from "react";

import { interpretNote } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

export function AnalystNoteForm({
  onSubmit,
  caseId,
}: {
  caseId: string;
  onSubmit: (payload: {
    note_type: string;
    affected_c: string;
    sentiment: string;
    risk_adjustment: number;
    content: string;
  }) => Promise<void>;
}) {
  const [noteType, setNoteType] = useState("management_meeting");
  const [affectedC, setAffectedC] = useState("Character");
  const [sentiment, setSentiment] = useState("neutral");
  const [riskAdjustment, setRiskAdjustment] = useState("0");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestion, setSuggestion] = useState<{
    affected_c: string;
    sentiment: string;
    risk_adjustment: number;
    rationale: string;
    signals: string[];
  } | null>(null);

  const handleSuggest = async () => {
    if (!content.trim()) return;
    setSuggesting(true);
    try {
      const inferred = await interpretNote(caseId, { note_type: noteType, content });
      setSuggestion(inferred);
      setAffectedC(inferred.affected_c);
      setSentiment(inferred.sentiment);
      setRiskAdjustment(String(inferred.risk_adjustment));
    } finally {
      setSuggesting(false);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit({
        note_type: noteType,
        affected_c: affectedC,
        sentiment,
        risk_adjustment: Number(riskAdjustment),
        content,
      });
      setContent("");
      setRiskAdjustment("0");
      setSuggestion(null);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="panel p-5 space-y-5">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#e91e8c]/15">
          <svg className="h-4.5 w-4.5 text-[#ff6bb5]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-bright">New Observation</h3>
          <p className="text-[11px] text-slate-dim">Record a qualitative note from field intelligence</p>
        </div>
      </div>

      <div className="h-px bg-[#4a1530]" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Select
          label="Note type"
          value={noteType}
          onChange={(event) => setNoteType(event.target.value)}
        >
          <option value="site_visit">Site visit</option>
          <option value="management_meeting">Management meeting</option>
          <option value="market_feedback">Market feedback</option>
          <option value="regulatory_observation">Regulatory observation</option>
          <option value="other">Other</option>
        </Select>
        <Select
          label="Affected C"
          value={affectedC}
          onChange={(event) => setAffectedC(event.target.value)}
        >
          <option value="Character">Character</option>
          <option value="Capacity">Capacity</option>
          <option value="Capital">Capital</option>
          <option value="Collateral">Collateral</option>
          <option value="Conditions">Conditions</option>
        </Select>
        <Select
          label="Sentiment"
          value={sentiment}
          onChange={(event) => setSentiment(event.target.value)}
        >
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </Select>
        <Input
          label="Risk adjustment"
          type="number"
          value={riskAdjustment}
          onChange={(event) => setRiskAdjustment(event.target.value)}
          placeholder="0"
        />
      </div>

      <Textarea
        label="Observation"
        rows={5}
        value={content}
        placeholder="Describe your observation, findings, or insights..."
        onChange={(event) => setContent(event.target.value)}
      />

      {suggestion && (
        <div className="rounded-xl border border-[#4a1530] bg-[#2d1420] p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.25em] text-slate-dim">Suggested Mapping</span>
            <span className="rounded-md bg-accent/15 px-2 py-1 text-[11px] text-accent-glow">{suggestion.affected_c}</span>
            <span className="rounded-md bg-gold/15 px-2 py-1 text-[11px] text-gold-glow">{suggestion.sentiment}</span>
            <span className="rounded-md bg-[#3d1a2a] px-2 py-1 text-[11px] text-slate">
              {suggestion.risk_adjustment > 0 ? "+" : ""}
              {suggestion.risk_adjustment}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate">{suggestion.rationale}</p>
          {suggestion.signals.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestion.signals.map((signal) => (
                <span
                  key={signal}
                  className="rounded-md border border-[#4a1530] bg-[#3d1a2a] px-2 py-1 text-[11px] text-slate"
                >
                  {signal}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-[11px] text-slate-dim">
          {content.length > 0 ? `${content.length} characters` : "Start typing your observation"}
        </p>
        <div className="flex items-center gap-3">
          <Button
            onClick={handleSuggest}
            disabled={!content.trim() || suggesting}
            variant="secondary"
          >
            {suggesting ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Interpreting...
              </>
            ) : (
              "Auto-map note"
            )}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!content.trim() || submitting}
            variant="primary"
          >
            {submitting ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add Note
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
