"""Background job runner for reconciliation processing.

Runs in a plain `threading.Thread` per session (no Celery/Redis — see
Docs/DEVELOPMENT_PLAN.md Section 2) and reports progress via the
`reconciliation_session.progress_pct` / `status` columns that the frontend polls.
"""
from __future__ import annotations

import logging
import threading
from decimal import Decimal

from app.database import SessionLocal
from app.models import LedgerEntry, MatchResult, ReconciliationSession, Txn
from app.services.matching import reconcile
from app.services.pdf_extraction import ExtractedRow, PdfExtractionError, extract_rows
from app.config import settings

logger = logging.getLogger(__name__)


def start_reconciliation_job(
    session_id: int,
    ledger_path: str | None,
    bank_paths_and_labels: list[tuple[str, str]],
) -> None:
    thread = threading.Thread(
        target=_run, args=(session_id, ledger_path, bank_paths_and_labels), daemon=True
    )
    thread.start()


def _set_progress(db, session: ReconciliationSession, pct: int, status: str | None = None) -> None:
    session.progress_pct = pct
    if status:
        session.status = status
    db.commit()


def _load_manual_ledger_rows(db, user_id: int) -> list[ExtractedRow]:
    entries = db.query(LedgerEntry).filter(LedgerEntry.user_id == user_id).order_by(LedgerEntry.txn_date).all()
    if not entries:
        raise PdfExtractionError("No saved ledger entries found")
    return [
        ExtractedRow(
            row_number=entry.id,
            txn_date=entry.txn_date,
            description=entry.description,
            amount_paise=entry.amount_paise,
            ref_no=entry.ref_no,
        )
        for entry in entries
    ]


def _run(session_id: int, ledger_path: str | None, bank_paths_and_labels: list[tuple[str, str]]) -> None:
    db = SessionLocal()
    try:
        session = db.get(ReconciliationSession, session_id)
        if session is None:
            return
        _set_progress(db, session, 5, "processing")

        if session.ledger_source == "manual":
            ledger_rows = _load_manual_ledger_rows(db, session.user_id)
        else:
            ledger_rows = extract_rows(ledger_path, settings.max_rows)
        _set_progress(db, session, 25)

        # Each bank statement is extracted separately (so a bad file gives a clear error) and
        # then tagged with its own label before being pooled for matching against one ledger.
        bank_rows: list[ExtractedRow] = []
        step = 30 / max(len(bank_paths_and_labels), 1)
        for i, (path, label) in enumerate(bank_paths_and_labels):
            rows = extract_rows(path, settings.max_rows)
            for row in rows:
                row.bank_label = label
            bank_rows.extend(rows)
            _set_progress(db, session, int(25 + step * (i + 1)))

        outcomes = reconcile(
            ledger_rows,
            bank_rows,
            session.date_tolerance_days,
            Decimal(str(session.amount_tolerance)),
            session.tolerance_type,
            session.description_threshold,
        )
        _set_progress(db, session, 80)

        _persist_results(db, session, ledger_rows, bank_rows, outcomes)
        _set_progress(db, session, 100, "done")
    except PdfExtractionError as exc:
        session = db.get(ReconciliationSession, session_id)
        if session:
            session.status = "error"
            session.error_message = str(exc)
            db.commit()
    except Exception as exc:  # noqa: BLE001 - convert any unexpected failure into a user-visible error
        logger.exception("Reconciliation job failed for session %s", session_id)
        session = db.get(ReconciliationSession, session_id)
        if session:
            session.status = "error"
            session.error_message = f"Unexpected error: {exc}"
            db.commit()
    finally:
        db.close()


def _persist_results(
    db,
    session: ReconciliationSession,
    ledger_rows: list[ExtractedRow],
    bank_rows: list[ExtractedRow],
    outcomes,
) -> None:
    txn_by_key: dict[tuple[str, int], Txn] = {}

    def _save_txn(row: ExtractedRow | None, source: str) -> Txn | None:
        if row is None:
            return None
        key = (source, row.row_number)
        if key in txn_by_key:
            return txn_by_key[key]
        txn = Txn(
            session_id=session.id,
            source=source,
            txn_date=row.txn_date,
            description=row.description,
            amount_paise=row.amount_paise,
            row_number=row.row_number,
            ref_no=row.ref_no,
            bank_label=row.bank_label if source == "bank" else None,
        )
        db.add(txn)
        db.flush()
        txn_by_key[key] = txn
        return txn

    for outcome in outcomes:
        ledger_txn = _save_txn(outcome.ledger_row, "ledger")
        bank_txn = _save_txn(outcome.bank_row, "bank")
        db.add(
            MatchResult(
                session_id=session.id,
                ledger_txn_id=ledger_txn.id if ledger_txn else None,
                bank_txn_id=bank_txn.id if bank_txn else None,
                match_status=outcome.status,
                reason=outcome.reason,
                tolerance_applied=outcome.tolerance_applied,
                is_duplicate=outcome.is_duplicate,
                date_diff_days=outcome.date_diff_days,
                amount_diff_paise=outcome.amount_diff_paise,
                similarity_score=outcome.similarity_score,
            )
        )
    db.commit()
