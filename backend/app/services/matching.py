"""Transaction matching engine — implements the revised algorithm in
Docs/DEVELOPMENT_PLAN.md Section 3.2 (candidate-collection + best-similarity
one-to-one assignment), replacing the naive first-candidate-wins flowchart.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from rapidfuzz import fuzz
from rapidfuzz.utils import default_process

from app.services.money import format_rupees
from app.services.pdf_extraction import ExtractedRow

DEFAULT_DESCRIPTION_THRESHOLD = 80.0


@dataclass
class MatchOutcome:
    ledger_row: ExtractedRow | None
    bank_row: ExtractedRow | None
    status: str  # Matched | Matched (tolerance) | Partial | Missing
    reason: str
    tolerance_applied: bool = False
    is_duplicate: bool = False
    date_diff_days: int | None = None
    amount_diff_paise: int | None = None
    similarity_score: float | None = None


def _signed_days_between(ledger_date: str, bank_date: str) -> int:
    """Positive when the bank date is later than the ledger date."""
    return (dt.date.fromisoformat(bank_date) - dt.date.fromisoformat(ledger_date)).days


def _similarity(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a, b, processor=default_process)


def _duplicate_groups(rows: list[ExtractedRow]) -> set[int]:
    """Return the set of row_numbers that belong to a (date, description, amount) group of size > 1."""
    groups: dict[tuple, list[ExtractedRow]] = {}
    for row in rows:
        key = (row.txn_date, row.description.strip().lower(), row.amount_paise)
        groups.setdefault(key, []).append(row)
    duplicates: set[int] = set()
    for group in groups.values():
        if len(group) > 1:
            duplicates.update(r.row_number for r in group)
    return duplicates


def reconcile(
    ledger_rows: list[ExtractedRow],
    bank_rows: list[ExtractedRow],
    date_tolerance_days: int,
    amount_tolerance: Decimal,
    tolerance_type: str,
    description_threshold: float = DEFAULT_DESCRIPTION_THRESHOLD,
) -> list[MatchOutcome]:
    """One-to-one greedy best-similarity matching. See Appendix A/C of the expected
    reconciliation report for the exact behaviour each branch must satisfy."""
    unconsumed_bank = list(bank_rows)
    results: list[MatchOutcome] = []

    sorted_ledger = sorted(ledger_rows, key=lambda r: r.txn_date)

    for ledger_row in sorted_ledger:
        candidates = []
        for bank_row in unconsumed_bank:
            date_diff = _signed_days_between(ledger_row.txn_date, bank_row.txn_date)
            if abs(date_diff) > date_tolerance_days:
                continue

            amount_diff = bank_row.amount_paise - ledger_row.amount_paise
            if tolerance_type == "percentage":
                allowed = Decimal(ledger_row.amount_paise) * amount_tolerance / 100
            else:
                allowed = amount_tolerance * 100  # rupees -> paise
            if abs(amount_diff) > allowed:
                continue

            score = _similarity(ledger_row.description, bank_row.description)
            candidates.append((bank_row, date_diff, amount_diff, score))

        if not candidates:
            results.append(MatchOutcome(ledger_row, None, "Missing", "Missing from bank"))
            continue

        # Best candidate: highest similarity, tie-break smallest |amount diff| then smallest |date diff|
        best_bank, best_date_diff, best_amount_diff, best_score = max(
            candidates, key=lambda c: (c[3], -abs(c[2]), -abs(c[1]))
        )
        unconsumed_bank.remove(best_bank)

        tolerance_applied = best_date_diff != 0 or best_amount_diff != 0
        if best_score >= description_threshold:
            status = "Matched (tolerance)" if tolerance_applied else "Matched"
            reason = _describe_tolerance(best_date_diff, best_amount_diff) if tolerance_applied else "Exact match"
        else:
            status = "Partial"
            reason = f"Description similarity {best_score:.0f}% < {description_threshold:.0f}%"

        results.append(
            MatchOutcome(
                ledger_row,
                best_bank,
                status,
                reason,
                tolerance_applied=tolerance_applied,
                date_diff_days=best_date_diff,
                amount_diff_paise=best_amount_diff,
                similarity_score=best_score,
            )
        )

    for bank_row in unconsumed_bank:
        results.append(MatchOutcome(None, bank_row, "Missing", "Missing from ledger"))

    # Duplicate detection runs independently on the ORIGINAL rows (Criterion C pseudocode step 3)
    ledger_dupes = _duplicate_groups(ledger_rows)
    bank_dupes = _duplicate_groups(bank_rows)
    for outcome in results:
        is_dup = (outcome.ledger_row is not None and outcome.ledger_row.row_number in ledger_dupes) or (
            outcome.bank_row is not None and outcome.bank_row.row_number in bank_dupes
        )
        if is_dup:
            outcome.is_duplicate = True
            outcome.reason = "Duplicate record" if outcome.status != "Missing" else f"{outcome.reason}; Duplicate record"

    return results


def _describe_tolerance(date_diff: int, amount_diff_paise: int) -> str:
    parts = []
    if date_diff != 0:
        sign = "+" if date_diff > 0 else "-"
        parts.append(f"date {sign}{abs(date_diff)}d")
    if amount_diff_paise != 0:
        sign = "+" if amount_diff_paise > 0 else "-"
        parts.append(f"amount {sign}{format_rupees(abs(amount_diff_paise))}")
    return "Matched with tolerance (" + ", ".join(parts) + ")"
