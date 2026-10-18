"""Pydantic request/response schemas."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class SessionCreateForm(BaseModel):
    date_tolerance_days: int = Field(ge=0, le=365, default=0)
    amount_tolerance: Decimal = Field(ge=0, default=Decimal("0"))
    tolerance_type: str = Field(default="absolute")
    description_threshold: float = Field(ge=0, le=100, default=80.0)

    @field_validator("tolerance_type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in ("absolute", "percentage"):
            raise ValueError("tolerance_type must be 'absolute' or 'percentage'")
        return v


class SessionOut(BaseModel):
    id: int
    ledger_filename: str
    bank_filename: str
    additional_bank_filenames: str | None = None
    ledger_source: str = "pdf"
    date_tolerance_days: int
    amount_tolerance: float
    tolerance_type: str
    description_threshold: float
    status: str
    progress_pct: int
    error_message: str | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ProgressOut(BaseModel):
    status: str
    progress_pct: int
    error_message: str | None = None


class TxnOut(BaseModel):
    txn_date: str
    description: str
    amount: str
    ref_no: str | None

    model_config = {"from_attributes": True}


class MatchResultOut(BaseModel):
    id: int
    date: str
    ledger_description: str | None
    ledger_amount: str | None
    bank_narration: str | None
    bank_amount: str | None
    bank_label: str | None = None
    match_status: str
    reason: str | None
    tolerance_applied: bool
    is_duplicate: bool
    similarity_score: float | None
    amount_diff: float | None = None
    date_diff_days: int | None = None


class SummaryOut(BaseModel):
    matched: int
    partial: int
    unmatched: int
    total: int


class ResultsPage(BaseModel):
    summary: SummaryOut
    items: list[MatchResultOut]
    page: int
    page_size: int
    total_items: int


class LedgerEntryIn(BaseModel):
    txn_date: str = Field(description="ISO date, YYYY-MM-DD")
    description: str = Field(min_length=1, max_length=300)
    amount: Decimal = Field(gt=0)
    ref_no: str | None = None

    @field_validator("txn_date")
    @classmethod
    def _check_date(cls, v: str) -> str:
        try:
            dt.date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("txn_date must be an ISO date (YYYY-MM-DD)") from exc
        return v


class LedgerEntryOut(BaseModel):
    id: int
    txn_date: str
    description: str
    amount: str
    ref_no: str | None
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = {"from_attributes": True}


class HistoryMatchOut(MatchResultOut):
    """A match result surfaced by the cross-session history search, with enough session
    context for the user to tell which reconciliation it came from and jump back to it."""

    session_id: int
    session_created_at: dt.datetime
    ledger_filename: str
    bank_filename: str
