# Reconciliation App

Web app to reconcile a business ledger against a bank statement (both uploaded as PDFs), with
configurable date/amount tolerances, fuzzy description matching, duplicate detection, a color-coded
results dashboard, and a downloadable PDF report.

Stack: **Angular 22** (frontend) · **FastAPI (Python)** (backend) · **SQLite** (database).
See [Docs/DEVELOPMENT_PLAN.md](Docs/DEVELOPMENT_PLAN.md) for the full architecture/design writeup.

## Project layout

```
backend/    FastAPI app, matching engine, PDF extraction, SQLite DB, tests
frontend/   Angular app (Material UI)
Docs/       Requirement docs, development plan, sample/expected data
```

## Prerequisites

- Python 3.11+ (developed/tested on 3.14)
- Node.js 20+ and npm (developed/tested on Node 24)

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests/ -v        # run tests (8 tests, incl. golden-CSV regression)
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

The API runs at `http://localhost:8000` (docs at `/docs`). SQLite DB and uploaded files are stored
under `backend/instance/` (auto-created).

## Frontend setup

```powershell
cd frontend
npm install
npm start   # ng serve --proxy-config proxy.conf.json, proxies /api to localhost:8000
```

Open `http://localhost:4200`. Register an account, then upload a ledger + bank statement PDF pair
and set tolerances to run a reconciliation.

## Test fixtures

`backend/tests/fixtures/generate_sample_pdfs.py` generates `ledger_aug2026.pdf` and
`bank_statement_aug2026.pdf` — synthetic PDFs transcribed from the sample documents in `Docs/`,
used to validate the extraction + matching pipeline against `Docs/expected_results_aug2026.csv`
(see `backend/tests/test_matching.py`).

## Key design decisions / deviations from the original spec

See [Docs/DEVELOPMENT_PLAN.md](Docs/DEVELOPMENT_PLAN.md) Section 1 for the full list of issues found
in the original Criterion A/B/C documentation and how they were resolved (e.g., money stored as
integer paise instead of float, nullable FKs on `match_result`, the corrected one-to-one best-match
algorithm, row-count/encryption validation checks, and FastAPI instead of Flask per user request).
