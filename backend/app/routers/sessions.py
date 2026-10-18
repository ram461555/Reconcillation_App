"""Reconciliation session endpoints: upload, progress polling, results, export, history."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, get_db
from app.models import LedgerEntry, MatchResult, ReconciliationSession, User
from app.schemas import HistoryMatchOut, MatchResultOut, ProgressOut, ResultsPage, SessionOut, SummaryOut
from app.services.money import format_rupees, paise_to_rupees
from app.services.validation import validate_pdf_upload
from app.services.pdf_extraction import PdfExtractionError
from app.background import start_reconciliation_job

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_owned_session(session_id: int, user: User, db: Session) -> ReconciliationSession:
    session = db.get(ReconciliationSession, session_id)
    if session is None or session.user_id != user.id:
        # 404 (not 403) so an attacker can't distinguish "doesn't exist" from "not yours" (IDOR mitigation)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    bank_file: UploadFile = File(...),
    bank_file_2: UploadFile | None = File(None),
    bank_file_3: UploadFile | None = File(None),
    ledger_file: UploadFile | None = File(None),
    use_manual_ledger: bool = Form(False),
    date_tolerance_days: int = Form(0),
    amount_tolerance: float = Form(0),
    tolerance_type: str = Form("absolute"),
    description_threshold: float = Form(80.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReconciliationSession:
    if tolerance_type not in ("absolute", "percentage"):
        raise HTTPException(status_code=422, detail="tolerance_type must be 'absolute' or 'percentage'")

    if not use_manual_ledger and ledger_file is None:
        raise HTTPException(status_code=400, detail="Upload a ledger PDF or choose 'use saved ledger entries'")
    if use_manual_ledger:
        has_entries = db.query(LedgerEntry).filter(LedgerEntry.user_id == current_user.id).first() is not None
        if not has_entries:
            raise HTTPException(status_code=400, detail="No saved ledger entries yet - add some in Ledger Management first")

    upload_dir = Path(settings.upload_dir) / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex

    ledger_path: str | None = None
    ledger_filename = "Saved ledger entries"
    if not use_manual_ledger:
        ledger_bytes = await ledger_file.read()
        try:
            validate_pdf_upload(ledger_file, "ledger", ledger_bytes)
        except PdfExtractionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        path = upload_dir / f"{token}_ledger.pdf"
        path.write_bytes(ledger_bytes)
        ledger_path = str(path)
        ledger_filename = ledger_file.filename

    bank_uploads = [f for f in (bank_file, bank_file_2, bank_file_3) if f is not None]
    if len(bank_uploads) > 3:
        raise HTTPException(status_code=400, detail="A maximum of 3 bank statements is supported")

    bank_paths_and_labels: list[tuple[str, str]] = []
    for upload in bank_uploads:
        data = await upload.read()
        try:
            validate_pdf_upload(upload, f"bank statement ({upload.filename})", data)
        except PdfExtractionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        path = upload_dir / f"{token}_bank_{len(bank_paths_and_labels)}.pdf"
        path.write_bytes(data)
        bank_paths_and_labels.append((str(path), upload.filename))

    session = ReconciliationSession(
        user_id=current_user.id,
        ledger_filename=ledger_filename,
        bank_filename=bank_paths_and_labels[0][1],
        additional_bank_filenames=", ".join(label for _, label in bank_paths_and_labels[1:]) or None,
        ledger_source="manual" if use_manual_ledger else "pdf",
        date_tolerance_days=date_tolerance_days,
        amount_tolerance=amount_tolerance,
        tolerance_type=tolerance_type,
        description_threshold=description_threshold,
        status="pending",
        progress_pct=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    start_reconciliation_job(session.id, ledger_path, bank_paths_and_labels)
    return session


@router.get("", response_model=list[SessionOut])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(ReconciliationSession)
        .filter(ReconciliationSession.user_id == current_user.id)
        .order_by(ReconciliationSession.created_at.desc())
        .all()
    )


@router.get("/{session_id}/progress", response_model=ProgressOut)
def get_progress(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(session_id, current_user, db)
    return ProgressOut(status=session.status, progress_pct=session.progress_pct, error_message=session.error_message)


@router.get("/{session_id}/results", response_model=ResultsPage)
def get_results(
    session_id: int,
    page: int = 1,
    page_size: int = 50,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_owned_session(session_id, current_user, db)
    if session.status != "done":
        raise HTTPException(status_code=409, detail=f"Session not ready (status={session.status})")

    query = db.query(MatchResult).filter(MatchResult.session_id == session.id)
    all_results = query.all()

    matched = sum(1 for r in all_results if r.match_status.startswith("Matched"))
    partial = sum(1 for r in all_results if r.match_status == "Partial")
    missing = sum(1 for r in all_results if r.match_status == "Missing")
    summary = SummaryOut(matched=matched, partial=partial, unmatched=missing, total=len(all_results))

    filtered = all_results
    if status_filter:
        filtered = [r for r in filtered if r.match_status == status_filter]

    def sort_key(r: MatchResult):
        return r.ledger_txn.txn_date if r.ledger_txn else (r.bank_txn.txn_date if r.bank_txn else "9999-99-99")

    filtered.sort(key=sort_key)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    items = [_to_result_out(r) for r in page_items]
    return ResultsPage(summary=summary, items=items, page=page, page_size=page_size, total_items=len(filtered))


def _to_result_out(r: MatchResult) -> MatchResultOut:
    ledger = r.ledger_txn
    bank = r.bank_txn
    return MatchResultOut(
        id=r.id,
        date=(ledger.txn_date if ledger else bank.txn_date if bank else ""),
        ledger_description=ledger.description if ledger else None,
        ledger_amount=format_rupees(ledger.amount_paise) if ledger else None,
        bank_narration=bank.description if bank else None,
        bank_amount=format_rupees(bank.amount_paise) if bank else None,
        bank_label=bank.bank_label if bank else None,
        match_status=r.match_status,
        reason=r.reason,
        tolerance_applied=r.tolerance_applied,
        is_duplicate=r.is_duplicate,
        similarity_score=r.similarity_score,
        amount_diff=float(paise_to_rupees(r.amount_diff_paise)) if r.amount_diff_paise is not None else None,
        date_diff_days=r.date_diff_days,
    )


@router.get("/history/search", response_model=list[HistoryMatchOut])
def search_history(
    date_from: str | None = None,
    date_to: str | None = None,
    amount_diff_min: float | None = None,
    date_diff_min: int | None = None,
    status_filter: str | None = None,
    duplicates_only: bool = False,
    tolerance_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cross-session search over every past reconciliation the user owns, combining several
    conditions at once (transaction date range, minimum amount/date difference, status,
    duplicate-only, tolerance-only) - the "Expand History section" advanced search."""
    results = (
        db.query(MatchResult)
        .join(ReconciliationSession, MatchResult.session_id == ReconciliationSession.id)
        .filter(ReconciliationSession.user_id == current_user.id)
        .filter(ReconciliationSession.status == "done")
        .all()
    )

    matches: list[HistoryMatchOut] = []
    for r in results:
        if status_filter and r.match_status != status_filter:
            continue
        if duplicates_only and not r.is_duplicate:
            continue
        if tolerance_only and not r.tolerance_applied:
            continue

        txn_date = r.ledger_txn.txn_date if r.ledger_txn else (r.bank_txn.txn_date if r.bank_txn else None)
        if date_from and (txn_date is None or txn_date < date_from):
            continue
        if date_to and (txn_date is None or txn_date > date_to):
            continue

        if amount_diff_min is not None:
            diff_rupees = abs(float(paise_to_rupees(r.amount_diff_paise))) if r.amount_diff_paise is not None else None
            if diff_rupees is None or diff_rupees < amount_diff_min:
                continue
        if date_diff_min is not None:
            diff_days = abs(r.date_diff_days) if r.date_diff_days is not None else None
            if diff_days is None or diff_days < date_diff_min:
                continue

        base = _to_result_out(r)
        session = r.session
        matches.append(
            HistoryMatchOut(
                **base.model_dump(),
                session_id=session.id,
                session_created_at=session.created_at,
                ledger_filename=session.ledger_filename,
                bank_filename=session.bank_filename,
            )
        )

    matches.sort(key=lambda m: m.date, reverse=True)
    return matches


@router.get("/{session_id}/export")
def export_pdf(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(session_id, current_user, db)
    if session.status != "done":
        raise HTTPException(status_code=409, detail=f"Session not ready (status={session.status})")

    from app.services.report import build_report_pdf  # local import avoids reportlab cost on startup

    results = db.query(MatchResult).filter(MatchResult.session_id == session.id).all()
    pdf_bytes = build_report_pdf(session, results)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="reconciliation_{session.id}.pdf"'},
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = _get_owned_session(session_id, current_user, db)
    db.delete(session)
    db.commit()
