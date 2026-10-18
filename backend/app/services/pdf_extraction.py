"""PDF table extraction, header column-mapping (rapidfuzz), and date/amount normalization.

Implements the File Upload Validation Flowchart pipeline from Docs/DEVELOPMENT_PLAN.md
Section 3.3, steps 4 (encrypted/corrupt check) and 6-9 (extraction, column mapping,
date normalisation, amount parsing).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pdfplumber
from rapidfuzz import fuzz, process

from app.services.money import parse_amount_to_paise


class PdfExtractionError(Exception):
    """Raised for any recoverable PDF/validation problem; message is user-facing."""


@dataclass
class ExtractedRow:
    row_number: int
    txn_date: str  # ISO YYYY-MM-DD
    description: str
    amount_paise: int
    ref_no: str | None
    bank_label: str | None = None  # which bank statement this row came from, when multiple are uploaded


_DATE_CANDIDATES = ["date", "txn date", "transaction date", "value date"]
_DESC_CANDIDATES = ["particulars", "description", "narration", "details"]
_AMOUNT_CANDIDATES = ["amount", "amount (inr)", "amt", "amount(inr)"]
_REF_CANDIDATES = ["voucher no.", "voucher no", "ref no.", "ref no", "reference", "cheque no"]

_DATE_FORMATS = ["%d/%m/%Y", "%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"]


def open_pdf_or_raise(file_path: str) -> pdfplumber.PDF:
    try:
        pdf = pdfplumber.open(file_path)
    except Exception as exc:  # pdfplumber/pypdf raise various types for encrypted/corrupt files
        message = str(exc).lower()
        if "password" in message or "encrypt" in message:
            raise PdfExtractionError("Password-protected PDF is not supported") from exc
        raise PdfExtractionError("Corrupted or unreadable PDF file") from exc
    if getattr(pdf, "is_encrypted", False):
        pdf.close()
        raise PdfExtractionError("Password-protected PDF is not supported")
    return pdf


def _best_header_match(header: str, candidates: list[str], threshold: int = 60) -> bool:
    if not header:
        return False
    match = process.extractOne(header.strip().lower(), candidates, scorer=fuzz.token_set_ratio)
    return bool(match and match[1] >= threshold)


def map_columns(header_row: list[str]) -> dict[str, int]:
    """Return {'date': idx, 'description': idx, 'amount': idx, 'ref_no': idx|None}."""
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(header_row):
        cell_clean = (cell or "").strip()
        if "date" not in mapping and _best_header_match(cell_clean, _DATE_CANDIDATES):
            mapping["date"] = idx
        elif "amount" not in mapping and _best_header_match(cell_clean, _AMOUNT_CANDIDATES):
            mapping["amount"] = idx
        elif "description" not in mapping and _best_header_match(cell_clean, _DESC_CANDIDATES):
            mapping["description"] = idx
        elif "ref_no" not in mapping and _best_header_match(cell_clean, _REF_CANDIDATES):
            mapping["ref_no"] = idx

    missing = [f for f in ("date", "description", "amount") if f not in mapping]
    if missing:
        raise PdfExtractionError(f"Unrecognized column headers, could not identify: {', '.join(missing)}")
    return mapping


def normalize_date(raw: str) -> str:
    raw = (raw or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    raise PdfExtractionError(f"Unrecognized date format: '{raw}'")


def extract_rows(file_path: str, max_rows: int) -> list[ExtractedRow]:
    """Extract, map, and normalize all table rows from a ledger/bank PDF."""
    pdf = open_pdf_or_raise(file_path)
    try:
        all_rows: list[list[str]] = []
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                all_rows.extend(table)
    finally:
        pdf.close()

    if not all_rows:
        raise PdfExtractionError("No tabular data found in PDF")

    header, *data_rows = all_rows
    mapping = map_columns(header)

    # Drop rows that are clearly not data: blank date cell, or a repeated header
    # row (multi-page tables re-print the header on every page).
    data_rows = [
        r for r in data_rows if r and (r[mapping["date"]] or "").strip() and r != header
    ]

    if len(data_rows) > max_rows:
        raise PdfExtractionError(f"Too many rows ({len(data_rows)}), max {max_rows} supported")

    if not data_rows:
        raise PdfExtractionError("No tabular data found in PDF")

    extracted: list[ExtractedRow] = []
    for i, row in enumerate(data_rows, start=1):
        try:
            txn_date = normalize_date(row[mapping["date"]])
            description = (row[mapping["description"]] or "").strip()
            amount_paise = parse_amount_to_paise(row[mapping["amount"]])
            ref_no = row[mapping["ref_no"]].strip() if "ref_no" in mapping and row[mapping["ref_no"]] else None
        except (PdfExtractionError, Exception) as exc:  # noqa: BLE001 - surfaced as a validation error
            raise PdfExtractionError(f"Row {i}: could not parse data ({exc})") from exc
        extracted.append(ExtractedRow(i, txn_date, description, amount_paise, ref_no))

    return extracted
