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


class SWOTItemRead(BaseModel):
    point: str
    evidence: str
    source: str


class SWOTRead(BaseModel):
    strengths: list[SWOTItemRead]
    weaknesses: list[SWOTItemRead]
    opportunities: list[SWOTItemRead]
    threats: list[SWOTItemRead]

