"""Basic upload validation: presence, size, and extension checks (steps 1-3 of the
File Upload Validation Flowchart in Docs/DEVELOPMENT_PLAN.md Section 3.3).
Steps 4+ (encryption/corruption, row limit, column mapping, normalisation) live in
app.services.pdf_extraction.
"""
from __future__ import annotations

from fastapi import UploadFile

from app.config import settings
from app.services.pdf_extraction import PdfExtractionError


def validate_pdf_upload(file: UploadFile | None, label: str, data: bytes) -> None:
    if file is None or not file.filename:
        raise PdfExtractionError(f"Missing file: {label}")
    if len(data) == 0:
        raise PdfExtractionError(f"Empty file: {label}")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise PdfExtractionError(f"File too large: {label} (max {settings.max_upload_mb}MB)")
    if not file.filename.lower().endswith(".pdf"):
        raise PdfExtractionError(f"Not a PDF: {label}")
    if data[:5] != b"%PDF-":
        raise PdfExtractionError(f"Not a valid PDF: {label}")
