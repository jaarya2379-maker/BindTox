from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("A valid email address is required.")
    local_part, domain = email.split("@", 1)
    if "." not in domain or not local_part or not domain:
        raise ValueError("A valid email address is required.")
    return email


class BreachRecord(BaseModel):
    breach_name: str
    email: str
    password_exposed: bool = False
    password_sha256: str | None = None
    breach_date: str
    source: str
    severity: Literal["low", "medium", "high", "critical"]
    data_types: list[str] = Field(default_factory=list)


class BreachCheckRequest(BaseModel):
    email: str
    password: str | None = Field(default=None, min_length=3)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class MitigationSuggestion(BaseModel):
    title: str
    action: str
    priority: Literal["low", "medium", "high"]


class PasswordExposureSummary(BaseModel):
    exposed: bool
    reused_password_risk: bool
    matched_breach_names: list[str] = Field(default_factory=list)


class RiskScoreBreakdown(BaseModel):
    score: int = Field(ge=0, le=100)
    rating: Literal["low", "guarded", "elevated", "critical"]
    reasons: list[str] = Field(default_factory=list)


class BreachCheckResponse(BaseModel):
    email: str
    breaches: list[BreachRecord] = Field(default_factory=list)
    password_summary: PasswordExposureSummary
    risk: RiskScoreBreakdown
    mitigation_suggestions: list[MitigationSuggestion] = Field(default_factory=list)
    checked_at: datetime


class AlertRecord(BaseModel):
    email: str
    risk_score: int
    breach_count: int
    created_at: datetime
    status: Literal["new", "investigating", "resolved"] = "new"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class DashboardSummary(BaseModel):
    monitored_accounts: int
    compromised_accounts: int
    critical_alerts: int
    average_risk_score: float
    latest_alerts: list[AlertRecord] = Field(default_factory=list)
