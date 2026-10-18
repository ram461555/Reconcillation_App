"""End-to-end API test: register -> login -> upload -> poll -> results -> export -> IDOR check."""
from __future__ import annotations

import time
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _wait_for_done(client, session_id: int, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/sessions/{session_id}/progress")
        assert resp.status_code == 200
        body = resp.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.1)
    raise TimeoutError("Reconciliation job did not finish in time")


def test_full_reconciliation_flow(client):
    # Register + login
    register_resp = client.post(
        "/api/auth/register",
        json={"username": "owner1", "email": "owner1@example.com", "password": "Sup3rSecret!"},
    )
    assert register_resp.status_code == 201, register_resp.text

    login_resp = client.post("/api/auth/login", json={"username": "owner1", "password": "Sup3rSecret!"})
    assert login_resp.status_code == 200, login_resp.text

    # Upload
    with open(FIXTURES_DIR / "ledger_aug2026.pdf", "rb") as lf, open(
        FIXTURES_DIR / "bank_statement_aug2026.pdf", "rb"
    ) as bf:
        upload_resp = client.post(
            "/api/sessions",
            files={
                "ledger_file": ("ledger_aug2026.pdf", lf, "application/pdf"),
                "bank_file": ("bank_statement_aug2026.pdf", bf, "application/pdf"),
            },
            data={
                "date_tolerance_days": "3",
                "amount_tolerance": "100",
                "tolerance_type": "absolute",
                "description_threshold": "80",
            },
        )
    assert upload_resp.status_code == 201, upload_resp.text
    session_id = upload_resp.json()["id"]

    progress = _wait_for_done(client, session_id)
    assert progress["status"] == "done", progress

    # Results
    results_resp = client.get(f"/api/sessions/{session_id}/results", params={"page_size": 100})
    assert results_resp.status_code == 200, results_resp.text
    payload = results_resp.json()
    assert payload["summary"] == {"matched": 24, "partial": 2, "unmatched": 12, "total": 38}
    assert len(payload["items"]) == 38

    # Export
    export_resp = client.get(f"/api/sessions/{session_id}/export")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/pdf"
    assert export_resp.content[:5] == b"%PDF-"

    # History
    history_resp = client.get("/api/sessions")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 1

    # IDOR check: a second user must not be able to access the first user's session
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register",
        json={"username": "owner2", "email": "owner2@example.com", "password": "Sup3rSecret!"},
    )
    client.post("/api/auth/login", json={"username": "owner2", "password": "Sup3rSecret!"})
    forbidden_resp = client.get(f"/api/sessions/{session_id}/results")
    assert forbidden_resp.status_code == 404


def test_rejects_non_pdf_upload(client):
    client.post(
        "/api/auth/register",
        json={"username": "owner3", "email": "owner3@example.com", "password": "Sup3rSecret!"},
    )
    client.post("/api/auth/login", json={"username": "owner3", "password": "Sup3rSecret!"})

    upload_resp = client.post(
        "/api/sessions",
        files={
            "ledger_file": ("ledger.txt", b"not a pdf", "text/plain"),
            "bank_file": ("bank.txt", b"not a pdf", "text/plain"),
        },
        data={"date_tolerance_days": "0", "amount_tolerance": "0", "tolerance_type": "absolute"},
    )
    assert upload_resp.status_code == 400


def test_requires_auth(client):
    client.post("/api/auth/logout")
    resp = client.get("/api/sessions")
    assert resp.status_code == 401
