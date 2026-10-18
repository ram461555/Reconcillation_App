"""Manual ledger entry endpoints (Ledger Management tab): lets a user maintain their ledger
inside the app instead of always re-uploading a PDF. Reconciliation sessions can then be run
against these saved entries by setting ledger_source='manual' on /api/sessions.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import LedgerEntry, User
from app.schemas import LedgerEntryIn, LedgerEntryOut
from app.services.money import parse_amount_to_paise, paise_to_rupees

router = APIRouter(prefix="/api/ledger", tags=["ledger"])


def _to_out(entry: LedgerEntry) -> LedgerEntryOut:
    return LedgerEntryOut(
        id=entry.id,
        txn_date=entry.txn_date,
        description=entry.description,
        amount=str(paise_to_rupees(entry.amount_paise)),
        ref_no=entry.ref_no,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _get_owned_entry(entry_id: int, user: User, db: Session) -> LedgerEntry:
    entry = db.get(LedgerEntry, entry_id)
    if entry is None or entry.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ledger entry not found")
    return entry


@router.get("", response_model=list[LedgerEntryOut])
def list_entries(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entries = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.user_id == current_user.id)
        .order_by(LedgerEntry.txn_date.desc(), LedgerEntry.id.desc())
        .all()
    )
    return [_to_out(e) for e in entries]


@router.post("", response_model=LedgerEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(payload: LedgerEntryIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = LedgerEntry(
        user_id=current_user.id,
        txn_date=payload.txn_date,
        description=payload.description,
        amount_paise=parse_amount_to_paise(str(payload.amount)),
        ref_no=payload.ref_no,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_out(entry)


@router.put("/{entry_id}", response_model=LedgerEntryOut)
def update_entry(
    entry_id: int,
    payload: LedgerEntryIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = _get_owned_entry(entry_id, current_user, db)
    entry.txn_date = payload.txn_date
    entry.description = payload.description
    entry.amount_paise = parse_amount_to_paise(str(payload.amount))
    entry.ref_no = payload.ref_no
    db.commit()
    db.refresh(entry)
    return _to_out(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = _get_owned_entry(entry_id, current_user, db)
    db.delete(entry)
    db.commit()
