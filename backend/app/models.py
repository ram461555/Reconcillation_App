"""ORM models matching the revised schema in Docs/DEVELOPMENT_PLAN.md (Section 3.1)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    sessions: Mapped[list["ReconciliationSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ReconciliationSession(Base):
    __tablename__ = "reconciliation_session"
    __table_args__ = (
        CheckConstraint("tolerance_type IN ('absolute','percentage')", name="ck_tolerance_type"),
        CheckConstraint("status IN ('pending','processing','done','error')", name="ck_status"),
        CheckConstraint("ledger_source IN ('pdf','manual')", name="ck_ledger_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    ledger_filename: Mapped[str]
    bank_filename: Mapped[str]
    additional_bank_filenames: Mapped[str | None] = mapped_column(default=None)  # comma-joined, bank #2/#3
    ledger_source: Mapped[str] = mapped_column(default="pdf")  # 'pdf' or 'manual' (saved ledger entries)
    file_hash: Mapped[str | None] = mapped_column(default=None)

    date_tolerance_days: Mapped[int] = mapped_column(default=0)
    amount_tolerance: Mapped[float] = mapped_column(default=0)
    tolerance_type: Mapped[str] = mapped_column(default="absolute")
    description_threshold: Mapped[float] = mapped_column(default=80)

    status: Mapped[str] = mapped_column(default="pending")
    progress_pct: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="sessions")
    transactions: Mapped[list["Txn"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    match_results: Mapped[list["MatchResult"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Txn(Base):
    __tablename__ = "txn"
    __table_args__ = (CheckConstraint("source IN ('ledger','bank')", name="ck_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("reconciliation_session.id", ondelete="CASCADE"))
    source: Mapped[str]
    txn_date: Mapped[str]  # ISO YYYY-MM-DD
    description: Mapped[str]
    amount_paise: Mapped[int]
    row_number: Mapped[int]
    ref_no: Mapped[str | None] = mapped_column(default=None)
    bank_label: Mapped[str | None] = mapped_column(default=None)  # which bank statement, when multiple uploaded

    session: Mapped["ReconciliationSession"] = relationship(back_populates="transactions")


class MatchResult(Base):
    __tablename__ = "match_result"
    __table_args__ = (
        CheckConstraint(
            "match_status IN ('Matched','Matched (tolerance)','Partial','Missing')", name="ck_match_status"
        ),
        CheckConstraint("ledger_txn_id IS NOT NULL OR bank_txn_id IS NOT NULL", name="ck_at_least_one_side"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("reconciliation_session.id", ondelete="CASCADE"))
    ledger_txn_id: Mapped[int | None] = mapped_column(ForeignKey("txn.id"), default=None)
    bank_txn_id: Mapped[int | None] = mapped_column(ForeignKey("txn.id"), default=None)

    match_status: Mapped[str]
    reason: Mapped[str | None] = mapped_column(default=None)  # semicolon-joined list
    tolerance_applied: Mapped[bool] = mapped_column(default=False)
    is_duplicate: Mapped[bool] = mapped_column(default=False)

    date_diff_days: Mapped[int | None] = mapped_column(default=None)
    amount_diff_paise: Mapped[int | None] = mapped_column(default=None)
    similarity_score: Mapped[float | None] = mapped_column(default=None)

    session: Mapped["ReconciliationSession"] = relationship(back_populates="match_results")
    ledger_txn: Mapped["Txn | None"] = relationship(foreign_keys=[ledger_txn_id])
    bank_txn: Mapped["Txn | None"] = relationship(foreign_keys=[bank_txn_id])


class LedgerEntry(Base):
    """A manually-maintained ledger row, independent of any PDF upload/session, so a user can build up
    and edit their ledger inside the app instead of always re-uploading a PDF (the "Ledger Management" tab).
    """

    __tablename__ = "ledger_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    txn_date: Mapped[str]  # ISO YYYY-MM-DD
    description: Mapped[str]
    amount_paise: Mapped[int]
    ref_no: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship()
