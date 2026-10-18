"""Generate the editable project code-and-setup guide as a Word document."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

DOCS_DIR = Path(__file__).parent
ROOT = DOCS_DIR.parent
OUT_PATH = DOCS_DIR / "Reconciliation_App_Code_and_Setup_Guide.docx"
DIAGRAM_PATH = DOCS_DIR / "reconciliation_flow_diagram.png"

BLUE = "#0D47A1"
LIGHT_BLUE = "#E3F2FD"
LIGHT_GRAY = "#F5F7FA"
DARK = RGBColor(0x26, 0x32, 0x38)


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_diagram() -> None:
    width, height = 1500, 1030
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = font(38, True)
    box_title = font(25, True)
    box_text = font(20)
    small = font(17)

    draw.text((50, 24), "Reconciliation App - End-to-End Flow", fill="#263238", font=title_font)

    boxes = [
        (80, 130, 380, 300, "Angular Frontend", ["Login / Register", "Upload PDFs + tolerances", "Poll progress", "Show results / export"]),
        (600, 130, 900, 300, "FastAPI API", ["Auth routes", "Session upload route", "Progress / results routes", "Ownership checks"]),
        (1120, 130, 1420, 300, "Browser Cookie", ["Signed JWT", "httpOnly", "Sent with API calls"]),
        (80, 430, 380, 660, "Validation + Extraction", ["PDF signature / size", "pdfplumber tables", "Header mapping", "Date + paise normalization"]),
        (600, 430, 900, 660, "Background Job", ["Candidate collection", "RapidFuzz scoring", "One-to-one matching", "Duplicate flagging"]),
        (1120, 430, 1420, 660, "SQLite Database", ["User", "ReconciliationSession", "Txn", "MatchResult"]),
        (360, 800, 680, 970, "Results API", ["Summary counts", "Paginated rows", "Status / reasons", "Progress percentage"]),
        (820, 800, 1140, 970, "Reportlab Export", ["Colour-coded PDF", "Matched / partial / missing", "Download response"]),
    ]

    def rounded(box, fill, outline="#1565C0"):
        draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=3)

    for x1, y1, x2, y2, heading, lines in boxes:
        rounded((x1, y1, x2, y2), LIGHT_BLUE)
        draw.text((x1 + 18, y1 + 16), heading, fill="#0D47A1", font=box_title)
        for i, line in enumerate(lines):
            draw.text((x1 + 22, y1 + 65 + i * 30), "- " + line, fill="#263238", font=box_text)

    def arrow(start, end, label=None):
        draw.line([start, end], fill="#455A64", width=5)
        import math
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        length = 18
        left = (end[0] - length * math.cos(angle - 0.5), end[1] - length * math.sin(angle - 0.5))
        right = (end[0] - length * math.cos(angle + 0.5), end[1] - length * math.sin(angle + 0.5))
        draw.polygon([end, left, right], fill="#455A64")
        if label:
            mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2 - 24)
            draw.text(mid, label, fill="#455A64", font=small)

    arrow((380, 210), (600, 210), "HTTP / JSON")
    arrow((900, 210), (1120, 210), "Set cookie")
    arrow((230, 300), (230, 430), "upload")
    arrow((750, 300), (750, 430), "start job")
    arrow((900, 545), (1120, 545), "persist")
    arrow((750, 660), (520, 800), "progress/results")
    arrow((900, 660), (980, 800), "export")
    arrow((520, 800), (380, 300), "poll / display")
    arrow((980, 800), (380, 300), "PDF download")

    image.save(DIAGRAM_PATH)


def shade(cell, color: str):
    props = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    props.append(shd)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 9, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, True, 9, (255, 255, 255))
        shade(table.rows[0].cells[i], BLUE)
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value), False, 8)
            if row_index % 2:
                shade(cells[i], LIGHT_GRAY)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Mm(width)
    doc.add_paragraph()
    return table


def add_code(doc, code: str):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    shade(cell, "263238")
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0xEC, 0xF0, 0xF1)
    doc.add_paragraph()


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(item)


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
    return p


def build_doc():
    make_diagram()
    doc = Document()
    for section in doc.sections:
        section.left_margin = Mm(17)
        section.right_margin = Mm(17)
        section.top_margin = Mm(16)
        section.bottom_margin = Mm(16)

    doc.core_properties.title = "Reconciliation App - Code and Setup Guide"
    doc.core_properties.subject = "Frontend, backend, database, flow diagram and local setup"
    doc.core_properties.author = "Reconciliation App"

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Reconciliation App\nCode, Architecture and Local Setup Guide")
    run.bold = True
    run.font.size = Pt(23)
    run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Angular 22  |  FastAPI  |  SQLAlchemy  |  SQLite").font.size = Pt(12)
    doc.add_picture(str(DIAGRAM_PATH), width=Inches(6.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Figure 1. End-to-end data flow through the application.").alignment = WD_ALIGN_PARAGRAPH.CENTER

    heading(doc, "1. Project Purpose", 1)
    doc.add_paragraph(
        "The application compares a ledger PDF with a bank-statement PDF. It extracts transaction rows, "
        "normalizes dates and money values, applies user-defined date and amount tolerances, compares "
        "descriptions using RapidFuzz, identifies missing and duplicate records, and produces a readable "
        "results table and downloadable PDF report."
    )
    add_table(doc, ["Layer", "Technology", "Main responsibility"], [
        ["Frontend", "Angular 22 + Angular Material", "Forms, file selection, progress polling, results dashboard, history"],
        ["Backend", "FastAPI + Python", "Authentication, validation, extraction, matching, persistence, export"],
        ["Database", "SQLite + SQLAlchemy", "Users, sessions, transactions and match results"],
        ["PDF processing", "pdfplumber + reportlab", "Extract input tables and generate reconciliation reports"],
        ["Matching", "RapidFuzz + integer paise arithmetic", "Best description match and exact tolerance comparisons"],
    ], [30, 48, 92])

    heading(doc, "2. Folder Structure", 1)
    add_code(doc, """Reconcillation_App/
|-- backend/
|   |-- main.py                    FastAPI application entrypoint
|   |-- requirements.txt           Python dependencies
|   |-- app/
|   |   |-- config.py              Settings and upload limits
|   |   |-- database.py             SQLAlchemy engine and SQLite pragmas
|   |   |-- models.py               ORM database models
|   |   |-- schemas.py              Pydantic API request/response models
|   |   |-- security.py             bcrypt and JWT helpers
|   |   |-- deps.py                 Database and current-user dependencies
|   |   |-- background.py            Reconciliation background job
|   |   |-- routers/auth.py         Register/login/logout/me routes
|   |   |-- routers/sessions.py     Upload/progress/results/export/history routes
|   |   `-- services/
|   |       |-- validation.py       Upload validation
|   |       |-- pdf_extraction.py   PDF table extraction and normalization
|   |       |-- matching.py          One-to-one matching algorithm
|   |       |-- money.py             Decimal-to-paise conversion
|   |       `-- report.py            Reportlab PDF output
|   |-- tests/                      Unit and API tests
|   `-- instance/                   SQLite database and uploaded files
|-- frontend/
|   `-- src/app/
|       |-- core/                   Models, API services, guard, interceptor
|       |-- features/auth/          Login and registration
|       |-- features/upload/        Upload and tolerance form
|       |-- features/results/       Summary and reconciliation table
|       |-- features/history/       Previous sessions
|       `-- shared/                 File-drop and status badge components
`-- Docs/                           Requirements, expected data and guides""")

    heading(doc, "3. Frontend Working", 1)
    doc.add_paragraph(
        "Angular is a single-page application. The router loads feature components without a full page "
        "reload. Angular Material provides the toolbar, cards, buttons, form fields, progress bar, table, "
        "chips and paginator."
    )
    heading(doc, "3.1 Application shell and routing", 2)
    doc.add_paragraph(
        "app.ts and app.html define the common toolbar. The toolbar shows Reconcile, History and Logout "
        "when Auth.currentUser is available. app.routes.ts lazy-loads Login, Register, Upload, Results and "
        "History. The authGuard checks the current authenticated user before protected routes are opened."
    )
    add_code(doc, """export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./features/auth/login/login')... },
  { path: 'upload', canActivate: [authGuard], loadComponent: () => import('./features/upload/upload')... },
  { path: 'results/:sessionId', canActivate: [authGuard], loadComponent: () => import('./features/results/results')... },
  { path: 'history', canActivate: [authGuard], loadComponent: () => import('./features/history/history')... }
];""")
    heading(doc, "3.2 Authentication service", 2)
    doc.add_paragraph(
        "core/services/auth.ts calls /api/auth/register, /login, /logout and /me. It stores the current "
        "user in an Angular signal. The browser keeps the signed JWT in an httpOnly cookie; the frontend "
        "does not store the password or token in localStorage. auth-interceptor.ts adds withCredentials to "
        "API requests and redirects to /login when the API returns HTTP 401."
    )
    heading(doc, "3.3 Upload and progress workflow", 2)
    doc.add_paragraph(
        "features/upload/upload.ts owns the reactive form and selected files. FileDrop validates the "
        "extension, empty-file condition and 10 MB client-side limit. Session.upload() builds a FormData "
        "request containing both PDFs and the tolerance fields. After the API returns a session id, Upload "
        "polls /api/sessions/{id}/progress approximately every 700 ms. When status becomes done, Angular "
        "navigates to /results/{id}."
    )
    heading(doc, "3.4 Results and history", 2)
    doc.add_paragraph(
        "The Results component requests the result page, calculates the visible filter/search view, and "
        "renders summary cards plus a Material table. Rows are styled by status: green for Matched, yellow "
        "for Partial, and red for Missing. The duplicate flag is shown as a separate status badge. The PDF "
        "export is an API URL for the current session. History calls GET /api/sessions and allows the user "
        "to reopen or delete a session."
    )

    heading(doc, "4. Backend Working", 1)
    heading(doc, "4.1 FastAPI startup", 2)
    doc.add_paragraph(
        "main.py creates the FastAPI application, imports the ORM models, creates database tables for a new "
        "installation, enables CORS for the Angular origin, registers the auth and session routers, and "
        "exposes /api/health."
    )
    add_code(doc, """app = FastAPI(title='Reconciliation App API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, ...)
app.include_router(auth.router)
app.include_router(sessions.router)""")
    heading(doc, "4.2 Authentication", 2)
    doc.add_paragraph(
        "auth.py creates users after checking unique username/email constraints. security.py hashes passwords "
        "with bcrypt and creates a signed JWT containing the user id and expiry. The token is returned in an "
        "httpOnly cookie. deps.py reads that cookie on protected requests and loads the User from SQLite."
    )
    heading(doc, "4.3 Upload route", 2)
    doc.add_paragraph(
        "POST /api/sessions accepts multipart/form-data. It reads the two files, validates the PDF signature, "
        "size and extension, writes the files under backend/instance/uploads/{user_id}, creates a pending "
        "ReconciliationSession, commits it, and starts the background job. The API returns immediately with "
        "the session id so the frontend can show progress."
    )
    heading(doc, "4.4 Background processing", 2)
    doc.add_paragraph(
        "background.py starts a daemon thread for each session. It updates progress at 5%, 30%, 55%, 80% and "
        "100%. It extracts ledger rows, extracts bank rows, calls reconcile(), persists Txn and MatchResult "
        "records, and changes the session status to done. Validation errors are stored in error_message and "
        "change the status to error."
    )
    add_code(doc, """ledger_rows = extract_rows(ledger_path, settings.max_rows)
bank_rows = extract_rows(bank_path, settings.max_rows)
outcomes = reconcile(ledger_rows, bank_rows, date_tolerance_days,
                     amount_tolerance, tolerance_type, description_threshold)
_persist_results(db, session, ledger_rows, bank_rows, outcomes)""")
    heading(doc, "4.5 PDF extraction and normalization", 2)
    doc.add_paragraph(
        "pdf_extraction.py opens the PDF with pdfplumber, extracts tables from every page, removes repeated "
        "header rows, maps date/description/amount/ref columns using RapidFuzz, parses dates into ISO "
        "YYYY-MM-DD strings, and converts Indian-formatted amounts such as 1,25,000.00 into integer paise. "
        "The mapping intentionally ignores extra columns such as Dr/Cr and Balance."
    )

    heading(doc, "5. Matching Algorithm", 1)
    doc.add_paragraph(
        "matching.py implements one-to-one greedy best-similarity matching. Ledger rows are sorted by date. "
        "For each ledger row, every unused bank row is tested against the inclusive date window and amount "
        "tolerance. Percentage tolerance is calculated from the ledger amount. Passing candidates are scored "
        "with RapidFuzz token_set_ratio. The highest score wins; ties prefer the smaller amount difference "
        "and then the smaller date difference. The winning bank row is removed from the available pool."
    )
    add_code(doc, """for ledger_row in sorted_ledger:
    candidates = [bank_row for bank_row in unconsumed_bank
                  if date_passes and amount_passes]
    if not candidates:
        results.append(Missing(ledger_row, 'Missing from bank'))
        continue
    best = max(candidates, key=description_similarity)
    unconsumed_bank.remove(best)
    results.append(Matched_or_Partial(ledger_row, best))

for bank_row in unconsumed_bank:
    results.append(Missing(bank_row, 'Missing from ledger'))

apply_duplicate_flags_to_original_rows()""")
    add_bullets(doc, [
        "Exact date and amount with similarity >= 80% becomes Matched.",
        "Date or amount within tolerance with similarity >= 80% becomes Matched (tolerance).",
        "Date and amount pass but similarity is below 80% becomes Partial.",
        "No candidate becomes Missing from bank; unused bank rows become Missing from ledger.",
        "Duplicate detection is independent and appends Duplicate record to the reason.",
    ])

    heading(doc, "6. Database Working", 1)
    doc.add_paragraph(
        "database.py creates the SQLAlchemy engine and session factory. Each SQLite connection enables "
        "PRAGMA foreign_keys=ON and journal_mode=WAL. WAL improves read concurrency while foreign-key "
        "enforcement protects relationships. SQLAlchemy ORM classes are defined in models.py."
    )
    add_table(doc, ["Table", "Important columns", "Purpose"], [
        ["user", "id, username, email, password_hash", "Stores account identity and bcrypt password hash."],
        ["reconciliation_session", "user_id, filenames, tolerances, status, progress_pct", "One reconciliation run and its settings."],
        ["txn", "session_id, source, txn_date, description, amount_paise", "Normalized ledger or bank transaction."],
        ["match_result", "nullable ledger_txn_id/bank_txn_id, status, reason, similarity", "Matched pair or one-sided missing result."],
    ], [38, 62, 70])
    doc.add_paragraph(
        "Amounts are stored as integer paise. For example, INR 25,000.00 is stored as 2,500,000 paise. "
        "This prevents binary floating-point rounding from changing a tolerance boundary comparison. Dates "
        "are stored as ISO strings so they sort consistently and are easy to serialize in JSON."
    )

    heading(doc, "7. API Flow", 1)
    add_table(doc, ["Method", "Endpoint", "What it does"], [
        ["POST", "/api/auth/register", "Creates a user with a bcrypt password hash."],
        ["POST", "/api/auth/login", "Verifies credentials and sets the signed JWT cookie."],
        ["GET", "/api/auth/me", "Returns the current authenticated user."],
        ["POST", "/api/sessions", "Validates/uploads PDFs, creates a session and starts processing."],
        ["GET", "/api/sessions/{id}/progress", "Returns status, percentage and any error message."],
        ["GET", "/api/sessions/{id}/results", "Returns summary and paginated match rows."],
        ["GET", "/api/sessions/{id}/export", "Generates and downloads the reportlab PDF."],
        ["GET", "/api/sessions", "Lists sessions belonging only to the current user."],
        ["DELETE", "/api/sessions/{id}", "Deletes an owned reconciliation session."],
    ], [28, 62, 80])

    heading(doc, "8. Local Setup", 1)
    doc.add_paragraph("Prerequisites")
    add_bullets(doc, [
        "Windows, macOS or Linux.",
        "Python 3.11 or newer. The project was tested with Python 3.14.",
        "Node.js 20 or newer and npm. The project was tested with Node.js 24 and npm 11.",
    ])
    heading(doc, "8.1 Backend setup", 2)
    add_code(doc, """# From the project root
cd backend

# Create an isolated Python environment
python -m venv .venv

# Windows PowerShell
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

# Run the backend tests
.\\.venv\\Scripts\\python.exe -m pytest tests/ -v

# Start the API
.\\.venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000""")
    doc.add_paragraph(
        "The backend is available at http://localhost:8000. FastAPI interactive documentation is at "
        "http://localhost:8000/docs. The SQLite file and uploaded files are created automatically under "
        "backend/instance/."
    )
    heading(doc, "8.2 Frontend setup", 2)
    add_code(doc, """# Open a second terminal from the project root
cd frontend
npm install
npm start""")
    doc.add_paragraph(
        "The Angular dev server runs at http://localhost:4200. frontend/proxy.conf.json forwards /api "
        "requests to http://localhost:8000, so the browser can call relative API URLs during development."
    )
    heading(doc, "8.3 Open the application", 2)
    add_bullets(doc, [
        "Open http://localhost:4200.",
        "Register a username, email and password.",
        "Upload a selectable-text ledger PDF and bank statement PDF.",
        "Set date tolerance, amount tolerance type/value and description threshold.",
        "Click Start reconciliation and wait for the progress bar to reach 100%.",
        "Review the result rows, filter/search them, open History, or export the report PDF.",
    ])

    heading(doc, "9. Testing and Verification", 1)
    add_code(doc, """# Backend regression and API tests
cd backend
.\\.venv\\Scripts\\python.exe -m pytest tests/ -v

# Frontend production build
cd ..\\frontend
npx ng build""")
    doc.add_paragraph(
        "The backend test suite covers authentication, PDF upload rejection, ownership/IDOR protection, "
        "PDF extraction, all three expected tolerance runs, ambiguous candidate pairing, duplicate rows, "
        "partial matches and missing transactions. The golden fixture is "
        "Docs/expected_results_aug2026.csv."
    )
    add_table(doc, ["Check", "Expected result"], [
        ["pytest tests/ -v", "8 tests pass, including golden CSV regression tests."],
        ["npx ng build", "Angular production bundle completes without compile errors."],
        ["POST /api/health", "Returns { status: ok }."],
        ["Run sample PDFs with date ±3 and absolute INR 100", "24 matched, 2 partial, 12 unmatched, total 38."],
    ], [75, 95])

    heading(doc, "10. Common Problems", 1)
    add_table(doc, ["Problem", "Resolution"], [
        ["python or node is not recognized", "Install Python/Node or refresh PATH, then reopen the terminal."],
        ["PowerShell blocks npm.ps1", "Run Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass, or use cmd.exe."],
        ["Port 8000 is already in use", "Stop the existing API or run uvicorn on another port and update proxy.conf.json."],
        ["Frontend shows API errors", "Confirm FastAPI is running on port 8000 before starting Angular."],
        ["PDF extraction fails", "Use selectable-text PDFs with a table containing date, description/particulars and amount columns."],
        ["Database needs resetting", "Stop the backend and remove backend/instance/reconciliation.db, then restart the API."],
    ], [65, 105])

    heading(doc, "11. Important Security Notes", 1)
    add_bullets(doc, [
        "Change JWT_SECRET before deploying outside local development.",
        "Serve the API over HTTPS in production and set the cookie secure flag to True.",
        "Keep uploaded financial PDFs outside the public frontend directory.",
        "All session routes filter by the authenticated user id to prevent cross-user access.",
        "Do not commit .env files, SQLite files, uploaded PDFs, or production secrets.",
    ])
    doc.add_paragraph(
        "The detailed design decisions and documentation corrections are recorded in "
        "Docs/DEVELOPMENT_PLAN.md and Docs/Required_Documentation_Changes.docx."
    )

    doc.save(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build_doc()
