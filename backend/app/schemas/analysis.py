from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CrossCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    check_name: str
    doc_a: str | None = None
    doc_b: str | None = None
    value_a: str | None = None
    value_b: str | None = None
    discrepancy: Decimal | None = None
    status: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class CFactorRead(BaseModel):
    signal: str
    impact: int | float
    evidence: str


class CScoreRead(BaseModel):
    score: int
    summary: str
    factors: list[CFactorRead]


class FiveCsRead(BaseModel):
    id: str
    case_id: str
    character: CScoreRead
    capacity: CScoreRead
    capital: CScoreRead
    collateral: CScoreRead
    conditions: CScoreRead
    overall_score: int
    risk_grade: str


class RecommendationRead(BaseModel):
    recommendation: str
    overall_score: int
    risk_grade: str
    recommended_amount_crore: Decimal | None = None
    recommended_rate_percent: Decimal | None = None
    recommended_tenure_months: int | None = None
    decision_reasoning: str
    key_strengths: list[dict]
    key_risks: list[dict]
    conditions_precedent: list[str]
    conditions_subsequent: list[str]
    monitoring_covenants: list[str]
    improvement_scenarios: list[dict] = []


class SWOTItemRead(BaseModel):
    point: str
    evidence: str
    source: str


class SWOTRead(BaseModel):
    strengths: list[SWOTItemRead]
    weaknesses: list[SWOTItemRead]
    opportunities: list[SWOTItemRead]
    threats: list[SWOTItemRead]


class MissingFieldRead(BaseModel):
    document_category: str
    field_key: str
    field_label: str
    document_id: str | None = None
    document_name: str | None = None


class ContradictionRead(BaseModel):
    id: str
    check_name: str
    status: str
    doc_a: str | None = None
    doc_b: str | None = None
    note: str | None = None
    value_a: str | None = None
    value_b: str | None = None


class ResearchDigestItemRead(BaseModel):
    id: str
    category: str
    title: str | None = None
    severity: str | None = None
    verification_status: str | None = None
    entity_scope: str | None = None
    match_explanation: str | None = None
    matched_terms: str | None = None
    source_url: str | None = None


class ResearchDigestRead(BaseModel):
    counts_by_status: dict[str, int]
    counts_by_scope: dict[str, int]
    verified_borrower_items: list[ResearchDigestItemRead]
    contextual_items: list[ResearchDigestItemRead]


class NoteImpactRead(BaseModel):
    id: str
    note_type: str | None = None
    affected_c: str | None = None
    sentiment: str | None = None
    risk_adjustment: int | None = None
    content: str


class AnalysisSummaryRead(BaseModel):
    case_id: str
    missing_required_fields: list[MissingFieldRead]
    contradictions: list[ContradictionRead]
    research_digest: ResearchDigestRead
    note_impacts: list[NoteImpactRead]
