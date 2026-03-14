from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class CaseBase(BaseModel):
    company_name: str
    cin: str | None = None
    pan: str | None = None
    sector: str | None = None
    subsector: str | None = None
    turnover_crore: Decimal | None = None
    incorporation_date: date | None = None
    registered_office: str | None = None
    loan_type: str | None = None
    loan_amount_crore: Decimal | None = None
    loan_tenure_months: int | None = None
    proposed_rate_percent: Decimal | None = None
    loan_purpose: str | None = None
    status: str | None = "onboarding"

    @field_validator(
        "incorporation_date", "turnover_crore", "loan_amount_crore",
        "loan_tenure_months", "proposed_rate_percent", mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    company_name: str | None = None
    cin: str | None = None
    pan: str | None = None
    sector: str | None = None
    subsector: str | None = None
    turnover_crore: Decimal | None = None
    incorporation_date: date | None = None
    registered_office: str | None = None
    loan_type: str | None = None
    loan_amount_crore: Decimal | None = None
    loan_tenure_months: int | None = None
    proposed_rate_percent: Decimal | None = None
    loan_purpose: str | None = None
    status: str | None = None

    @field_validator(
        "incorporation_date", "turnover_crore", "loan_amount_crore",
        "loan_tenure_months", "proposed_rate_percent", mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CaseRead(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

