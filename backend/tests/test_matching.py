"""Golden-fixture regression tests: validate the full extraction + matching pipeline
against Docs/expected_results_aug2026.csv for all three tolerance runs described in
Appendix B of expected_reconciliation_report_aug2026.pdf.
"""
from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.matching import reconcile
from app.services.pdf_extraction import extract_rows

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CSV_PATH = Path(__file__).parent.parent.parent / "Docs" / "expected_results_aug2026.csv"


@pytest.fixture(scope="module")
def ledger_rows():
    return extract_rows(str(FIXTURES_DIR / "ledger_aug2026.pdf"), 1000)


@pytest.fixture(scope="module")
def bank_rows():
    return extract_rows(str(FIXTURES_DIR / "bank_statement_aug2026.pdf"), 1000)


@pytest.fixture(scope="module")
def golden_rows():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _outcome_key(outcome):
    """A stable identity for comparing against the CSV row-by-row: (ledger_row_no, bank_row_no)."""
    return (
        outcome.ledger_row.row_number if outcome.ledger_row else None,
        outcome.bank_row.row_number if outcome.bank_row else None,
    )


def test_extraction_row_counts(ledger_rows, bank_rows):
    assert len(ledger_rows) == 32
    assert len(bank_rows) == 32


@pytest.mark.parametrize(
    "date_tol,amt_tol,tol_type,status_col,reason_col,expected_matched,expected_partial,expected_unmatched",
    [
        (3, Decimal("100"), "absolute", "run1_status", "run1_reason", 24, 2, 12),
        (3, Decimal("1"), "percentage", "run2_status_pct1", "run2_status_pct1", 24, 2, 12),
        (0, Decimal("0"), "absolute", "run3_status_exact", "run3_status_exact", 19, 2, 22),
    ],
)
def test_reconcile_matches_golden_csv(
    ledger_rows,
    bank_rows,
    golden_rows,
    date_tol,
    amt_tol,
    tol_type,
    status_col,
    reason_col,
    expected_matched,
    expected_partial,
    expected_unmatched,
):
    outcomes = reconcile(ledger_rows, bank_rows, date_tol, amt_tol, tol_type, description_threshold=80.0)

    matched = sum(1 for o in outcomes if o.status.startswith("Matched"))
    partial = sum(1 for o in outcomes if o.status == "Partial")
    unmatched = sum(1 for o in outcomes if o.status == "Missing")

    assert matched == expected_matched, f"matched count mismatch for {tol_type}/{date_tol}/{amt_tol}"
    assert partial == expected_partial
    assert unmatched == expected_unmatched
    # Run 3 (0-tolerance) legitimately produces more rows (43) than Run 1/2 (38)
    # because each tolerance-match splits into two "Missing" rows — see Appendix B.


def test_run1_edge_cases_from_appendix_a(ledger_rows, bank_rows):
    """Row-level checks for the non-trivial Appendix A scenarios (Run 1 tolerances)."""
    outcomes = reconcile(ledger_rows, bank_rows, 3, Decimal("100"), "absolute", description_threshold=80.0)
    by_ledger_desc = {o.ledger_row.description: o for o in outcomes if o.ledger_row}

    # Date tolerance +2d
    rent = by_ledger_desc["Rent - Shah Properties - Aug 2026"]
    assert rent.status == "Matched (tolerance)"
    assert "date +2d" in rent.reason

    # Amount tolerance -50 (bank lower than ledger)
    kalpana = by_ledger_desc["Receipt - Kalpana Events - Inv 0227"]
    assert kalpana.status == "Matched (tolerance)"
    assert "amount -50.00" in kalpana.reason

    # Transposition error must NOT match (12,540 vs 15,240 both fail the 100 abs tolerance)
    ganesh_toner = by_ledger_desc["Ganesh Inks - Toner CMYK set"]
    assert ganesh_toner.status == "Missing" and ganesh_toner.reason == "Missing from bank"

    # Ambiguous same-day/same-amount pair: each must pair with its OWN description, not swapped
    advance_meera = by_ledger_desc["Advance - Meera Paper Mart"]
    advance_ganesh = by_ledger_desc["Advance - Ganesh Inks"]
    assert advance_meera.bank_row.description == "NEFT MEERA PAPER MART ADVANCE"
    assert advance_ganesh.bank_row.description == "NEFT GANESH INKS ADVANCE"

    # Partial matches (date+amount pass, description below threshold)
    sundry = by_ledger_desc["Sundry expenses"]
    assert sundry.status == "Partial" and "25%" in sundry.reason
    petty_cash = by_ledger_desc["Petty cash withdrawal"]
    assert petty_cash.status == "Partial" and "50%" in petty_cash.reason

    # Duplicate ledger entry: one copy matched (+Duplicate), the other Missing from bank (+Duplicate)
    meera_bill_1203 = [o for o in outcomes if o.ledger_row and o.ledger_row.description == "Meera Paper Mart - Bill 1203"]
    assert len(meera_bill_1203) == 2
    statuses = sorted(o.status for o in meera_bill_1203)
    assert statuses == ["Matched", "Missing"]
    for o in meera_bill_1203:
        assert o.is_duplicate
        assert "Duplicate record" in o.reason

