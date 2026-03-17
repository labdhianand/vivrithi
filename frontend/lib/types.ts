export type CaseStatus =
  | "onboarding"
  | "documents_uploaded"
  | "extracting"
  | "extracted"
  | "analyzing"
  | "report_ready";

export interface CaseRecord {
  id: string;
  company_name: string;
  cin?: string | null;
  pan?: string | null;
  sector?: string | null;
  subsector?: string | null;
  turnover_crore?: string | null;
  incorporation_date?: string | null;
  registered_office?: string | null;
  loan_type?: string | null;
  loan_amount_crore?: string | null;
  loan_tenure_months?: number | null;
  proposed_rate_percent?: string | null;
  loan_purpose?: string | null;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentRecord {
  id: string;
  case_id: string;
  original_filename: string;
  stored_path: string;
  file_size_bytes?: number | null;
  mime_type?: string | null;
  sha256_hash?: string | null;
  auto_category?: string | null;
  auto_category_confidence?: string | null;
  user_category?: string | null;
  classification_status: string;
  processing_status: string;
  failure_reason?: string | null;
  current_stage: string;
  progress_percent: number;
  total_pages?: number | null;
  raw_markdown?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageRecord {
  id: string;
  document_id: string;
  page_number: number;
  is_scanned?: boolean | null;
  has_tables?: boolean | null;
  content_type?: string | null;
  parser_used?: string | null;
  raw_text?: string | null;
  raw_markdown?: string | null;
  page_image_path?: string | null;
  parsing_confidence?: string | null;
  parsing_duration_ms?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ExtractionRecord {
  id: string;
  document_id: string;
  page_id?: string | null;
  schema_field_key: string;
  field_label?: string | null;
  value?: string | null;
  value_type?: string | null;
  value_numeric?: string | null;
  source_page_number?: number | null;
  bbox_x1?: string | null;
  bbox_y1?: string | null;
  bbox_x2?: string | null;
  bbox_y2?: string | null;
  confidence?: string | null;
  extraction_method?: string | null;
  user_verified: boolean;
  user_edited_value?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SchemaField {
  key: string;
  label: string;
  type: string;
  required: boolean;
  description?: string | null;
}

export interface SchemaRecord {
  id: string;
  case_id?: string | null;
  document_category: string;
  schema_version: number;
  fields: SchemaField[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResearchItem {
  id: string;
  case_id: string;
  category: string;
  title?: string | null;
  summary?: string | null;
  source_url?: string | null;
  source_name?: string | null;
  published_date?: string | null;
  sentiment?: string | null;
  severity?: string | null;
  relevance_score?: string | null;
  affected_c?: string | null;
  impact_description?: string | null;
  entity_scope?: string | null;
  entity_match_score?: string | null;
  verification_status?: string | null;
  matched_terms?: string | null;
  match_explanation?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalystNote {
  id: string;
  case_id: string;
  note_type?: string | null;
  content: string;
  affected_c?: string | null;
  sentiment?: string | null;
  risk_adjustment?: number | null;
  created_at: string;
  updated_at: string;
}

export interface AnalystNoteInterpretation {
  affected_c: string;
  sentiment: string;
  risk_adjustment: number;
  rationale: string;
  signals: string[];
}

export interface EvidenceRef {
  kind: "extraction" | "research" | "analyst_note" | string;
  label?: string | null;
  document_id?: string | null;
  document_name?: string | null;
  document_category?: string | null;
  page_number?: number | null;
  extraction_id?: string | null;
  schema_field_key?: string | null;
  research_id?: string | null;
  note_id?: string | null;
  url?: string | null;
  source_name?: string | null;
  content?: string | null;
  verification_status?: string | null;
  entity_scope?: string | null;
}

export interface CFactor {
  signal: string;
  impact: number;
  evidence: string;
  evidence_refs?: EvidenceRef[];
}

export interface CScore {
  score: number;
  summary: string;
  factors: CFactor[];
}

export interface FiveCs {
  id: string;
  case_id: string;
  character: CScore;
  capacity: CScore;
  capital: CScore;
  collateral: CScore;
  conditions: CScore;
  overall_score: number;
  risk_grade: string;
}

export interface Recommendation {
  recommendation: string;
  overall_score: number;
  risk_grade: string;
  recommended_amount_crore?: string | null;
  recommended_rate_percent?: string | null;
  recommended_tenure_months?: number | null;
  decision_reasoning: string;
  key_strengths: { title: string; detail: string; evidence_refs?: EvidenceRef[] }[];
  key_risks: { title: string; detail: string; evidence_refs?: EvidenceRef[] }[];
  conditions_precedent: string[];
  conditions_subsequent: string[];
  monitoring_covenants: string[];
  improvement_scenarios: { title: string; detail: string; priority: string }[];
}

export interface SWOTItem {
  point: string;
  evidence: string;
  source: string;
}

export interface SWOT {
  strengths: SWOTItem[];
  weaknesses: SWOTItem[];
  opportunities: SWOTItem[];
  threats: SWOTItem[];
}

export interface CrossCheck {
  id: string;
  case_id: string;
  check_name: string;
  doc_a?: string | null;
  doc_b?: string | null;
  value_a?: string | null;
  value_b?: string | null;
  discrepancy?: string | null;
  status: string;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisSummary {
  case_id: string;
  missing_required_fields: Array<{
    document_category: string;
    field_key: string;
    field_label: string;
    document_id?: string | null;
    document_name?: string | null;
  }>;
  contradictions: Array<{
    id: string;
    check_name: string;
    status: string;
    doc_a?: string | null;
    doc_b?: string | null;
    note?: string | null;
    value_a?: string | null;
    value_b?: string | null;
  }>;
  research_digest: {
    counts_by_status: Record<string, number>;
    counts_by_scope: Record<string, number>;
    verified_borrower_items: Array<{
      id: string;
      category: string;
      title?: string | null;
      severity?: string | null;
      verification_status?: string | null;
      entity_scope?: string | null;
      match_explanation?: string | null;
      matched_terms?: string | null;
      source_url?: string | null;
    }>;
    contextual_items: Array<{
      id: string;
      category: string;
      title?: string | null;
      severity?: string | null;
      verification_status?: string | null;
      entity_scope?: string | null;
      match_explanation?: string | null;
      matched_terms?: string | null;
      source_url?: string | null;
    }>;
  };
  note_impacts: Array<{
    id: string;
    note_type?: string | null;
    affected_c?: string | null;
    sentiment?: string | null;
    risk_adjustment?: number | null;
    content: string;
  }>;
}

export interface ReportRecord {
  id: string;
  case_id: string;
  report_type: string;
  format: string;
  stored_path?: string | null;
  sections?: Array<{ id: string; title: string; content_markdown: string; evidence_refs?: EvidenceRef[] }>;
  created_at: string;
  updated_at: string;
}
