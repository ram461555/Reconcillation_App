"""One-off script to generate Required_Documentation_Changes.pdf (in this same Docs/ folder).
Not part of the application; run manually with the backend venv's Python:
    ..\\backend\\.venv\\Scripts\\python.exe generate_required_changes_doc.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = Path(__file__).parent / "Required_Documentation_Changes.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=20, spaceAfter=4)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#455a64"), spaceAfter=18)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=15, spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#0d47a1"))
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1565c0"))
body = ParagraphStyle("BodyX", parent=styles["BodyText"], fontSize=9.5, leading=13)
cell = ParagraphStyle("Cell", parent=styles["BodyText"], fontSize=8.5, leading=11)
cell_bold = ParagraphStyle("CellBold", parent=cell, fontName="Helvetica-Bold")
note_style = ParagraphStyle("Note", parent=styles["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#5d4037"), backColor=colors.HexColor("#fff8e1"), borderPadding=6, spaceBefore=6, spaceAfter=10)


def P(text: str, style=cell) -> Paragraph:
    return Paragraph(text, style)


def change_table(rows: list[tuple[str, str, str]]) -> Table:
    """rows: (original, required_change, reason)"""
    header = [P("Original documentation", cell_bold), P("Required change", cell_bold), P("Reason", cell_bold)]
    data = [header] + [[P(a), P(b), P(c)] for a, b, c in rows]
    t = Table(data, colWidths=[55 * mm, 60 * mm, 60 * mm], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d47a1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
            ]
        )
    )
    return t


doc = SimpleDocTemplate(
    str(OUT_PATH),
    pagesize=A4,
    leftMargin=16 * mm,
    rightMargin=16 * mm,
    topMargin=16 * mm,
    bottomMargin=16 * mm,
)

elements = []

elements.append(Paragraph("Required Documentation Changes", title_style))
elements.append(
    Paragraph(
        "Criterion A, B and C currently describe React + Flask + PostgreSQL. The application was actually "
        "built with Angular + FastAPI + SQLite (per your instruction), and several corrections were needed "
        "in the ERD, algorithm and validation flowcharts to make the design actually satisfy its own success "
        "criteria and test cases. This document lists every change your write-up needs so the documentation "
        "matches the working system.",
        subtitle_style,
    )
)

# ---------------------------------------------------------------------------
elements.append(Paragraph("1. Criterion A \u2014 Problem Specification", h1))

elements.append(Paragraph("1.1 Computational Context \u2014 tech stack bullets", h2))
elements.append(
    change_table(
        [
            (
                "\u201cFor the GUI React.js and Bootstrap will be used.\u201d",
                "Replace with: \u201cFor the GUI Angular and Angular Material will be used.\u201d Keep the same "
                "justification (SPA behaviour without full page reloads, pre-built components) \u2014 it applies "
                "equally to Angular Material.",
                "Frontend framework changed from React to Angular for this build.",
            ),
            (
                "\u201cI will be using flask as the web framework\u2026 I choose it over Django as it's "
                "lightweight and minimal\u2026\u201d",
                "Replace with: \u201cI will be using FastAPI as the web framework. I choose it over Flask/Django "
                "because it is lightweight like Flask, but adds native async support, automatic request "
                "validation via Pydantic, and auto-generated OpenAPI docs \u2014 useful when the frontend is a "
                "separate Angular SPA calling a typed JSON API.\u201d",
                "Backend framework changed from Flask to FastAPI for this build.",
            ),
            (
                "\u201cPostgreSQL for the database as it handles multi-user access, strong data integrity "
                "through ACID transactions and has role-based access control so only authorised users can "
                "access the sensitive financial data\u201d",
                "Replace with: \u201cSQLite for the database as it needs no separate server process, is fully "
                "file-based (simple to back up/ship with the app), and still gives ACID transactions for a "
                "single-server small-business deployment. Authorisation (which user may see which session) is "
                "enforced at the application layer instead of via database roles, since SQLite has no "
                "built-in role-based access control.\u201d",
                "Database changed from PostgreSQL to SQLite. SQLite genuinely has no role-based access "
                "control or robust multi-writer concurrency \u2014 the original justification no longer holds "
                "and must not be copied over unchanged.",
            ),
            (
                "\u201cAnd libraries like pandas (data manipulation and reconciliation logic), pdfplumber "
                "(extract tabular data from the PDF files) and rapidfuzz (row and column matching) are "
                "necessary\u2026\u201d",
                "Either (a) remove pandas from this sentence, keeping only pdfplumber and rapidfuzz, or (b) if "
                "you want to keep pandas for the mark scheme, explicitly use a pandas DataFrame somewhere in "
                "the matching step of the implementation so the documentation matches the code.",
                "The working matching engine does not use pandas \u2014 rows are handled as plain Python "
                "objects for precise integer (paise) arithmetic. Documentation should not list a library that "
                "isn't actually used.",
            ),
        ]
    )
)

elements.append(Paragraph("1.2 Success Criteria", h2))
elements.append(
    change_table(
        [
            (
                "\u201cTolerance: \u2026 difference up to 100 or percentage difference up to 3%\u201d",
                "Add a clarifying clause: \u201cPercentage tolerance is always computed against the ledger "
                "amount (not the bank amount), and both absolute and percentage tolerances are inclusive at "
                "the boundary (a difference exactly equal to the tolerance still counts as a match).\u201d",
                "This rule is required for the matching algorithm to behave deterministically, but was never "
                "stated as a success criterion, only implied later in supporting material.",
            ),
            (
                "\u201cPerformance: \u2026 process and reconcile up to 500 transactions in 10-20 seconds\u201d",
                "Add: \u201cIf either uploaded file exceeds a configurable row limit (1000 rows), the app "
                "rejects the upload with an error message instead of attempting to process it.\u201d",
                "The Testing Strategy already expects an error for a 10,000-row file, but no success "
                "criterion or flowchart ever defines the cut-off that causes that error.",
            ),
        ]
    )
)

elements.append(PageBreak())

# ---------------------------------------------------------------------------
elements.append(Paragraph("2. Criterion B \u2014 Planning", h1))

elements.append(Paragraph("2.1 Decomposition", h2))
elements.append(
    change_table(
        [
            (
                "1. User Authentication and Security \u2013 \u201cHash passwords using werkzeug.security before "
                "storing in the database\u201d",
                "Replace with: \u201cHash passwords using bcrypt directly before storing in the database.\u201d",
                "werkzeug is a Flask dependency; FastAPI has no equivalent built in, and bcrypt can be called "
                "directly without an extra abstraction layer.",
            ),
            (
                "1. User Authentication and Security \u2013 \u201cSet a secret key in Flask to cryptographically "
                "sign session cookies\u201d",
                "Replace with: \u201cSign a JWT (containing the user id and an expiry) with a secret key, and "
                "store it in an httpOnly cookie set by the API on login.\u201d",
                "FastAPI does not have Flask's built-in server-side session/cookie-signing mechanism; "
                "authentication state is carried in a signed JWT instead.",
            ),
            (
                "2. File Upload and Validation \u2013 \u201cMake a file upload component in React\u201d / "
                "\u201cDefine the POST route in Flask\u201d",
                "Replace \u201cReact\u201d with \u201cAngular\u201d and \u201cFlask\u201d with \u201cFastAPI\u201d "
                "throughout this section.",
                "Tech stack change.",
            ),
            (
                "3. Data extraction and Structuring \u2013 \u201cConvert the extracted data into pandas "
                "dataframes for reconciliation\u201d",
                "Replace with: \u201cConvert the extracted data into a list of plain Python row objects for "
                "reconciliation.\u201d",
                "Matches the actual implementation (no pandas dependency in the matching engine).",
            ),
            (
                "4. Transaction matching and Tolerance handling \u2013 \u201cMake the matching logic in pandas "
                "to compare rows from the two dataframes\u201d",
                "Replace with: \u201cFor each ledger row, collect every bank row that passes the date and "
                "amount tolerance, score each candidate's description similarity with rapidfuzz, and assign "
                "the ledger row to the single best-scoring candidate (removing it from the pool so it cannot "
                "be reused by another ledger row).\u201d",
                "The original one-line description (\u201ccompare rows\u201d) allows a naive first-match "
                "implementation, which fails on same-day/same-amount ambiguous pairs (see Criterion C, "
                "Section 3.3 of this document).",
            ),
            (
                "6/7. \u201cCreate a tolerance input in react\u201d / \u201cBuild upload, reconcile, export, "
                "history buttons and pages using react\u201d",
                "Replace \u201creact\u201d with \u201cAngular\u201d.",
                "Tech stack change.",
            ),
            (
                "7. \u201cDisplay the reconciliation table with colour coded rows (green, yellow, red) using "
                "Bootstrap\u201d",
                "Replace \u201cBootstrap\u201d with \u201cAngular Material\u201d.",
                "Tech stack change.",
            ),
            (
                "7. \u201cDisplay a progress bar in react while Flask is processing the PDFs\u201d",
                "Replace with: \u201cDisplay a progress bar in Angular that polls a FastAPI endpoint for "
                "percentage-complete while the PDFs are processed in a background task.\u201d",
                "Tech stack change, and clarifies the polling mechanism (no server push was implemented).",
            ),
        ]
    )
)

elements.append(Paragraph("2.2 Planning table (Week 1-2 row)", h2))
elements.append(
    change_table(
        [
            (
                "\u201cSetup Flask, PostgreSQL, SQLAlchemy and React\u201d",
                "Replace with: \u201cSetup FastAPI, SQLite, SQLAlchemy and Angular\u201d",
                "Tech stack change; SQLAlchemy is unchanged as it works identically over SQLite.",
            )
        ]
    )
)

elements.append(PageBreak())

# ---------------------------------------------------------------------------
elements.append(Paragraph("3. Criterion C \u2014 System Overview", h1))

elements.append(Paragraph("3.1 ERD (Image 3)", h2))
elements.append(
    change_table(
        [
            (
                "MATCH_RESULT.ledger_txn_id (FK) and bank_txn_id (FK) shown as ordinary, implicitly "
                "required foreign keys",
                "Make both columns nullable, and add a table-level rule: at least one of ledger_txn_id / "
                "bank_txn_id must be present.",
                "Rows describing a transaction that is \u201cMissing from bank\u201d or \u201cMissing from "
                "ledger\u201d only have one side populated \u2014 the ERD as drawn cannot represent them.",
            ),
            (
                "MATCH_RESULT has columns: id, session_id, ledger_txn_id, bank_txn_id, match_status, reason, "
                "tolerance_applied",
                "Add three more columns: date_diff_days (integer), amount_diff (numeric), similarity_score "
                "(numeric, 0-100).",
                "The reconciliation report shows the day difference, amount difference and description "
                "similarity % for every row \u2014 without storing these, the report/export cannot be "
                "regenerated from the database.",
            ),
            (
                "TRANSACTION.amount is typed as float",
                "Change to an integer column storing the amount in paise (minor currency units), e.g. "
                "\u20b9250.00 stored as 25000.",
                "Binary floating point cannot exactly represent amounts like 0.01 or 0.10, which risks a "
                "difference that should be exactly on a tolerance boundary being read as very slightly over "
                "or under it. Integer paise avoids this entirely.",
            ),
            (
                "RECONCILIATION_SESSION has columns: id, user_id, ledger_filename, bank_filename, "
                "date_tolerance_days, amount_tolerance, tolerance_type, status, created_at",
                "Add: progress_pct (integer 0-100), error_message (string, nullable), description_threshold "
                "(numeric, default 80).",
                "The progress bar (sequence diagram / SC \u201cUser interface and feedback\u201d) needs "
                "somewhere to read percentage-complete from, error handling needs somewhere to store *why* a "
                "session failed, and the description-match threshold is a user-configurable value that isn't "
                "captured anywhere in the current schema.",
            ),
        ]
    )
)

elements.append(Paragraph("3.2 Sequence diagram", h2))
elements.append(
    change_table(
        [
            (
                "Lane labelled \u201cFlask Server\u201d",
                "Rename to \u201cFastAPI Server\u201d.",
                "Backend framework change.",
            ),
            (
                "\u201cStart confirmed\u201d step implies a session-cookie is set by Flask's built-in session "
                "handling",
                "Clarify: the server returns a signed JWT which the browser stores as an httpOnly cookie; "
                "this cookie is sent automatically on the later \u201cCheck progress\u201d and \u201cGet final "
                "results\u201d calls.",
                "FastAPI has no built-in session store like Flask \u2014 the diagram should show the actual "
                "auth mechanism used.",
            ),
        ]
    )
)

elements.append(Paragraph("3.3 Transaction Matching Flowchart", h2))
elements.append(
    Paragraph(
        "The current flowchart iterates ledger rows one at a time and, for each one, validates date then "
        "amount then fuzzy-matches description against what looks like a single bank row, marking it "
        "MATCHED or Partial and moving straight to the next ledger row. This does not work once more than "
        "one bank row can pass the date+amount check for the same ledger row.",
        body,
    )
)
elements.append(
    change_table(
        [
            (
                "Steps 4-6 (\u201cValidate Date\u201d \u2192 \u201cValidate Amount\u201d \u2192 \u201cFuzzy "
                "Matching\u201d) operate on one candidate bank row per ledger row, first-match wins",
                "Replace with: for each ledger row, first collect every bank row (not yet used by an earlier "
                "ledger row) that passes both the date and amount tolerance into a candidate list. If the "
                "list is empty, mark the ledger row \u201cMissing from bank\u201d. Otherwise, fuzzy-match the "
                "description against every candidate and keep only the single highest-scoring one; mark that "
                "bank row as used so no other ledger row can claim it. Then apply the existing "
                "\u226580%/<80% split for Matched vs Partial.",
                "With a naive first-match approach, two ledger rows and two bank rows that share the same "
                "date and amount (e.g. two advance payments made on the same day for the same amount to "
                "different suppliers) can be paired with the wrong counterpart, because the algorithm never "
                "compares descriptions across all candidates before committing to a match.",
            ),
            (
                "No explicit statement that a bank row, once matched, is removed from the pool of candidates",
                "Add a note/step: \u201ca bank row that has been assigned to a ledger row (whether Matched or "
                "Partial) is removed from the candidate pool and cannot be assigned to any other ledger "
                "row.\u201d",
                "Without this rule the same bank transaction could satisfy two different ledger entries, "
                "which is not one-to-one reconciliation.",
            ),
        ]
    )
)

elements.append(Paragraph("3.4 File Upload Validation Flowchart", h2))
elements.append(
    change_table(
        [
            (
                "No step checks the uploaded file's size before extraction",
                "Insert a check immediately after \u201cCheck: Extension is .pdf?\u201d: \u201cCheck: file size "
                "> 0 bytes?\u201d \u2192 No: \u201cError: empty file\u201d.",
                "The Testing Strategy has a dedicated \u201cUpload empty 0-byte file\u201d test case expecting "
                "an error message, but no flowchart step produces that error.",
            ),
            (
                "No step limits how many rows can be extracted before matching begins",
                "Insert a check after \u201cExtract tables\u201d: \u201cCheck: row count \u2264 maximum "
                "supported (e.g. 1000)?\u201d \u2192 No: \u201cError: too many rows\u201d.",
                "The Testing Strategy expects a 10,000-row file to produce an error, but Success Criteria "
                "only promises performance up to 500 rows \u2014 the flowchart needs an explicit cut-off that "
                "causes the rejection.",
            ),
            (
                "\u201cCheck: Tables extracted?\u201d \u2192 No \u2192 \u201cError: no tables or corrupt PDF\u201d "
                "is the only handling for unreadable PDFs",
                "Add a separate, earlier check right after opening the file: \u201cCan the PDF be opened "
                "without a password?\u201d \u2192 No: \u201cError: password-protected or corrupted PDF\u201d.",
                "Opening an encrypted PDF raises a different kind of error than \u201cno tables found\u201d "
                "and should be caught explicitly \u2014 the Testing Strategy has its own row for "
                "password-protected PDFs.",
            ),
        ]
    )
)

elements.append(Paragraph("3.5 Pseudocode", h2))
elements.append(
    change_table(
        [
            (
                "\u201chashed = werkzeug.generate_password_hash(password)\u201d",
                "Replace with: \u201chashed = bcrypt.hashpw(password, bcrypt.gensalt())\u201d",
                "werkzeug is Flask-specific; bcrypt is called directly instead.",
            ),
            (
                "\u201cSET session cookie with user.id\u201d / \u201cRETURN redirect to /reconcile\u201d",
                "Replace with: \u201ctoken = create_jwt({'sub': user.id}, secret_key, expiry)\u201d and "
                "\u201cSET httpOnly cookie with token; RETURN user profile as JSON\u201d.",
                "FastAPI serves a JSON API for the Angular SPA to call, rather than performing a "
                "server-rendered redirect; the SPA's router (not the server) decides which page to show "
                "next.",
            ),
        ]
    )
)

elements.append(Paragraph("3.6 Testing Strategy \u2014 rows to add", h2))
elements.append(
    change_table(
        [
            (
                "(not currently present)",
                "Automatic Matching / Normal: two ledger rows and two bank rows share the same date and "
                "amount but different descriptions \u2192 expected result: each ledger row pairs with the "
                "bank row that has the closer-matching description, not simply the first candidate found.",
                "Directly tests the corrected matching algorithm in Section 3.3 above.",
            ),
            (
                "(not currently present)",
                "Security / Abnormal: a logged-in user requests another user's session id directly by URL "
                "\u2192 expected result: request is rejected (not found), not returned.",
                "Confirms sessions are private per-user, which the current Security row (login redirect "
                "only) does not cover.",
            ),
            (
                "(not currently present)",
                "Tolerance / Normal: percentage tolerance is confirmed to be calculated from the ledger "
                "amount, not the bank amount.",
                "The percentage-tolerance rule is used by the matching algorithm but was never written down "
                "as something to test.",
            ),
        ]
    )
)

elements.append(Paragraph("3.7 GUI screens", h2))
elements.append(
    change_table(
        [
            (
                "Screens use Bootstrap-style components in the wireframe captions",
                "Update captions/labels to Angular Material equivalents (e.g. \u201cmat-card\u201d, "
                "\u201cmat-table\u201d, \u201cmat-progress-bar\u201d) instead of Bootstrap component names.",
                "Tech stack change.",
            ),
            (
                "Nav bar mockup on Screen 2 includes a \u201cHistory\u201d link, but no History screen is "
                "designed anywhere in Criterion C",
                "Add a 4th wireframe: \u201cScreen 4 \u2013 History\u201d showing a list of past reconciliation "
                "sessions (date, file names, tolerance used, summary counts) with an action to re-open each "
                "one.",
                "Closes a gap between the navigation design and the screens that were actually specified.",
            ),
        ]
    )
)

elements.append(Spacer(1, 14))
elements.append(
    Paragraph(
        "Full technical detail (revised SQL schema, corrected matching pseudocode, REST API contract) is in "
        "Docs/DEVELOPMENT_PLAN.md, which was used as the basis for the implementation that these "
        "documentation changes are being aligned to.",
        note_style,
    )
)

doc.build(elements)
print("Wrote", OUT_PATH)
