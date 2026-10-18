"""Generate the reconciliation PDF report (matches the layout of
Docs/expected_reconciliation_report_aug2026.pdf) using reportlab.
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet

from app.models import MatchResult, ReconciliationSession
from app.services.money import format_rupees

_STATUS_COLORS = {
    "Matched": colors.HexColor("#d7f0d8"),
    "Matched (tolerance)": colors.HexColor("#d7f0d8"),
    "Partial": colors.HexColor("#fff3cd"),
    "Missing": colors.HexColor("#fbdada"),
}


def build_report_pdf(session: ReconciliationSession, results: list[MatchResult]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Reconciliation Report", styles["Title"]))
    elements.append(
        Paragraph(
            f"Ledger file: {session.ledger_filename} &nbsp;&nbsp; "
            f"Bank statement: {session.bank_filename}",
            styles["Normal"],
        )
    )
    tolerance_desc = (
        f"date window \u00b1{session.date_tolerance_days} days, "
        f"amount tolerance {session.amount_tolerance} "
        f"({session.tolerance_type}). Description threshold "
        f"{session.description_threshold:.0f}%."
    )
    elements.append(Paragraph(tolerance_desc, styles["Normal"]))
    elements.append(Spacer(1, 8))

    matched = sum(1 for r in results if r.match_status.startswith("Matched"))
    partial = sum(1 for r in results if r.match_status == "Partial")
    missing = sum(1 for r in results if r.match_status == "Missing")
    total = len(results)
    summary_data = [["Matched", "Partial", "Unmatched", "Total"], [matched, partial, missing, total]]
    summary_table = Table(summary_data, colWidths=[100] * 4)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    header = ["#", "Date", "Ledger particulars", "Ledger (INR)", "Bank (INR)", "Bank narration", "Status", "Reason", "Sim %"]
    rows = [header]
    row_colors = []
    for i, r in enumerate(sorted(results, key=_sort_key), start=1):
        ledger = r.ledger_txn
        bank = r.bank_txn
        rows.append(
            [
                str(i),
                (ledger.txn_date if ledger else bank.txn_date if bank else ""),
                ledger.description if ledger else "\u2014",
                format_rupees(ledger.amount_paise) if ledger else "\u2014",
                format_rupees(bank.amount_paise) if bank else "\u2014",
                bank.description if bank else "\u2014",
                r.match_status,
                r.reason or "",
                f"{r.similarity_score:.0f}" if r.similarity_score is not None else "\u2014",
            ]
        )
        row_colors.append(_STATUS_COLORS.get(r.match_status, colors.white))

    table = Table(rows, repeatRows=1, colWidths=[20, 55, 140, 60, 60, 150, 70, 140, 30])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for idx, color in enumerate(row_colors, start=1):
        style.append(("BACKGROUND", (0, idx), (-1, idx), color))
    table.setStyle(TableStyle(style))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


def _sort_key(r: MatchResult):
    date = r.ledger_txn.txn_date if r.ledger_txn else (r.bank_txn.txn_date if r.bank_txn else "9999-99-99")
    return date
