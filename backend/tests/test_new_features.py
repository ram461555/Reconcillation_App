"""Tests for the new feedback-driven features: manual ledger entries, multi-bank-statement
reconciliation, and the cross-session history search endpoint.
"""
from __future__ import annotations

import time
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _register_and_login(client, username: str) -> None:
    client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "Sup3rSecret!"},
    )
    client.post("/api/auth/login", json={"username": username, "password": "Sup3rSecret!"})


def _wait_for_done(client, session_id: int, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/sessions/{session_id}/progress")
        body = resp.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.1)
    raise TimeoutError("job did not finish in time")


def test_ledger_entry_crud(client):
    _register_and_login(client, "ledgeruser")

    create_resp = client.post(
        "/api/ledger",
        json={"txn_date": "2026-08-01", "description": "Rent - Shah Properties", "amount": "25000.00", "ref_no": "PAY-01"},
    )
    assert create_resp.status_code == 201, create_resp.text
    entry_id = create_resp.json()["id"]
    assert create_resp.json()["amount"] == "25000.00"

    list_resp = client.get("/api/ledger")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.put(
        f"/api/ledger/{entry_id}",
        json={"txn_date": "2026-08-02", "description": "Rent - Shah Properties (updated)", "amount": "26000.00", "ref_no": None},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"].endswith("(updated)")
    assert update_resp.json()["amount"] == "26000.00"

    delete_resp = client.delete(f"/api/ledger/{entry_id}")
    assert delete_resp.status_code == 204
    assert client.get("/api/ledger").json() == []


def test_reconcile_against_manual_ledger(client):
    _register_and_login(client, "manualledgeruser")

    # Two entries that match two rows in the bank statement fixture exactly.
    client.post(
        "/api/ledger",
        json={"txn_date": "2026-08-04", "description": "Electricity bill - Adani - Jul 2026", "amount": "6842.00"},
    )
    client.post(
        "/api/ledger",
        json={"txn_date": "2026-08-25", "description": "Stationery - Kamal Stores", "amount": "1875.00"},
    )

    with open(FIXTURES_DIR / "bank_statement_aug2026.pdf", "rb") as bf:
        upload_resp = client.post(
            "/api/sessions",
            files={"bank_file": ("bank_statement_aug2026.pdf", bf, "application/pdf")},
            data={"use_manual_ledger": "true", "date_tolerance_days": "0", "amount_tolerance": "0", "tolerance_type": "absolute"},
        )
    assert upload_resp.status_code == 201, upload_resp.text
    session = upload_resp.json()
    assert session["ledger_source"] == "manual"

    progress = _wait_for_done(client, session["id"])
    assert progress["status"] == "done", progress

    results = client.get(f"/api/sessions/{session['id']}/results", params={"page_size": 100}).json()
    assert results["summary"]["matched"] == 2
    assert results["summary"]["unmatched"] == 30  # 32 bank rows - 2 matched = 30 "Missing from ledger"


def test_reconcile_with_multiple_bank_statements(client):
    _register_and_login(client, "multibankuser")

    with open(FIXTURES_DIR / "ledger_aug2026.pdf", "rb") as lf, open(
        FIXTURES_DIR / "bank_statement_aug2026.pdf", "rb"
    ) as bf1, open(FIXTURES_DIR / "bank_statement_aug2026.pdf", "rb") as bf2:
        upload_resp = client.post(
            "/api/sessions",
            files={
                "ledger_file": ("ledger_aug2026.pdf", lf, "application/pdf"),
                "bank_file": ("hdfc.pdf", bf1, "application/pdf"),
                "bank_file_2": ("icici.pdf", bf2, "application/pdf"),
            },
            data={"date_tolerance_days": "3", "amount_tolerance": "100", "tolerance_type": "absolute"},
        )
    assert upload_resp.status_code == 201, upload_resp.text
    session = upload_resp.json()
    assert session["bank_filename"] == "hdfc.pdf"
    assert session["additional_bank_filenames"] == "icici.pdf"

    progress = _wait_for_done(client, session["id"])
    assert progress["status"] == "done", progress

    # Bank rows are duplicated across the two "banks" (same fixture file twice), so the two
    # identical "Meera Paper Mart Bill 1203" ledger rows can now BOTH find a bank match (one from
    # each bank file) instead of the second one being left "Missing from bank" as in the
    # single-bank run - proving the two bank files are pooled together for one ledger.
    results = client.get(f"/api/sessions/{session['id']}/results", params={"page_size": 200}).json()
    assert results["summary"]["matched"] + results["summary"]["partial"] == 27  # one more match than single-bank (26)
    assert results["summary"]["total"] > 38  # extra unmatched rows from the duplicated second bank file


def test_history_search_filters(client):
    _register_and_login(client, "historysearchuser")

    with open(FIXTURES_DIR / "ledger_aug2026.pdf", "rb") as lf, open(
        FIXTURES_DIR / "bank_statement_aug2026.pdf", "rb"
    ) as bf:
        upload_resp = client.post(
            "/api/sessions",
            files={
                "ledger_file": ("ledger_aug2026.pdf", lf, "application/pdf"),
                "bank_file": ("bank_statement_aug2026.pdf", bf, "application/pdf"),
            },
            data={"date_tolerance_days": "3", "amount_tolerance": "100", "tolerance_type": "absolute"},
        )
    session_id = upload_resp.json()["id"]
    _wait_for_done(client, session_id)

    # No filters: everything from this session's Matched/Partial/Missing rows should be searchable.
    all_matches = client.get("/api/sessions/history/search").json()
    assert len(all_matches) >= 38
    assert all(m["session_id"] == session_id for m in all_matches)

    # Duplicate-only filter should surface exactly the two duplicate Meera Paper Mart rows.
    dup_only = client.get("/api/sessions/history/search", params={"duplicates_only": True}).json()
    assert len(dup_only) == 2
    assert all(m["is_duplicate"] for m in dup_only)

    # Date range restricted to a single day should only return that day's rows.
    single_day = client.get(
        "/api/sessions/history/search", params={"date_from": "2026-08-20", "date_to": "2026-08-20"}
    ).json()
    assert len(single_day) >= 1
    assert all(m["date"] == "2026-08-20" for m in single_day)

    # A second user must not see the first user's history.
    _register_and_login(client, "historysearchuser2")
    other_view = client.get("/api/sessions/history/search").json()
    assert other_view == []
