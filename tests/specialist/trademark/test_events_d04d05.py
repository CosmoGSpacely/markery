"""Tests for D004 (events table) and D005 (foreign_app table).

Uses in-memory DuckDB with CSV files written to a temp directory so no
real CSV dataset is required.
"""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb
import pytest

from markery.specialist.trademark.build import open_db, load_events, load_foreign_app, _ENRICHMENT_DDL
from markery.specialist.trademark.queries import get_events, get_foreign_apps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mem_db() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    conn.execute(_ENRICHMENT_DDL)
    # Minimal case_file for serial filter
    conn.execute("""
        CREATE TABLE IF NOT EXISTS case_file (
            serial_no VARCHAR PRIMARY KEY,
            filing_dt DATE
        )
    """)
    return conn


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# D004: load_events
# ---------------------------------------------------------------------------

def test_load_events_inserts_filtered_rows(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")
    conn.execute("INSERT INTO case_file VALUES ('71000002','1921-01-01')")

    _write_csv(tmp_path / "event.csv", [
        {"serial_no": "71000001", "event_dt": "1920-06-01", "event_cd": "NDOA",
         "event_desc_t": "New application filed", "party_cd": "AP"},
        {"serial_no": "71000002", "event_dt": "1921-03-01", "event_cd": "PUBT",
         "event_desc_t": "Published for opposition", "party_cd": "OA"},
        {"serial_no": "99999999", "event_dt": "1930-01-01", "event_cd": "NDOA",
         "event_desc_t": "Not in case_file", "party_cd": "AP"},
    ])

    n = load_events(tmp_path, conn)
    assert n == 2


def test_load_events_replaces_on_reload(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")

    _write_csv(tmp_path / "event.csv", [
        {"serial_no": "71000001", "event_dt": "1920-06-01", "event_cd": "NDOA",
         "event_desc_t": "First load", "party_cd": "AP"},
    ])
    load_events(tmp_path, conn)

    _write_csv(tmp_path / "event.csv", [
        {"serial_no": "71000001", "event_dt": "1920-06-01", "event_cd": "NDOA",
         "event_desc_t": "Second load A", "party_cd": "AP"},
        {"serial_no": "71000001", "event_dt": "1921-01-01", "event_cd": "PUBT",
         "event_desc_t": "Second load B", "party_cd": "OA"},
    ])
    n = load_events(tmp_path, conn)
    assert n == 2


def test_get_events_returns_records(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")
    _write_csv(tmp_path / "event.csv", [
        {"serial_no": "71000001", "event_dt": "1920-06-01", "event_cd": "NDOA",
         "event_desc_t": "New application", "party_cd": "AP"},
        {"serial_no": "71000001", "event_dt": "1921-01-01", "event_cd": "PUBT",
         "event_desc_t": "Published", "party_cd": "OA"},
    ])
    load_events(tmp_path, conn)

    results = get_events(conn, "71000001")
    assert len(results) == 2
    assert results[0]["event_cd"] == "NDOA"
    assert results[1]["event_cd"] == "PUBT"


def test_get_events_returns_empty_for_missing(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")
    _write_csv(tmp_path / "event.csv", [
        {"serial_no": "71000001", "event_dt": "1920-06-01", "event_cd": "NDOA",
         "event_desc_t": "New app", "party_cd": "AP"},
    ])
    load_events(tmp_path, conn)
    assert get_events(conn, "00000000") == []


def test_get_events_empty_table():
    conn = _mem_db()
    assert get_events(conn, "71000001") == []


# ---------------------------------------------------------------------------
# D005: load_foreign_app
# ---------------------------------------------------------------------------

def test_load_foreign_app_inserts_filtered_rows(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")

    _write_csv(tmp_path / "foreign_application.csv", [
        {"serial_no": "71000001", "foreign_appl_no": "GB12345",
         "foreign_country_cd": "GB", "foreign_filing_dt": "1919-06-01",
         "foreign_reg_no": "UK9876", "foreign_reg_dt": "1920-01-01"},
        {"serial_no": "99999999", "foreign_appl_no": "DE99999",
         "foreign_country_cd": "DE", "foreign_filing_dt": "1919-01-01",
         "foreign_reg_no": None, "foreign_reg_dt": None},
    ])

    n = load_foreign_app(tmp_path, conn)
    assert n == 1


def test_load_foreign_app_replaces_on_reload(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")

    row = {"serial_no": "71000001", "foreign_appl_no": "GB12345",
           "foreign_country_cd": "GB", "foreign_filing_dt": "1919-06-01",
           "foreign_reg_no": None, "foreign_reg_dt": None}
    _write_csv(tmp_path / "foreign_application.csv", [row])
    load_foreign_app(tmp_path, conn)
    load_foreign_app(tmp_path, conn)
    n = conn.execute("SELECT count(*) FROM foreign_app").fetchone()[0]
    assert n == 1


def test_get_foreign_apps_returns_records(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")
    _write_csv(tmp_path / "foreign_application.csv", [
        {"serial_no": "71000001", "foreign_appl_no": "GB12345",
         "foreign_country_cd": "GB", "foreign_filing_dt": "1919-06-01",
         "foreign_reg_no": "UK9876", "foreign_reg_dt": "1920-01-01"},
    ])
    load_foreign_app(tmp_path, conn)

    results = get_foreign_apps(conn, "71000001")
    assert len(results) == 1
    assert results[0]["foreign_country_cd"] == "GB"
    assert results[0]["foreign_appl_no"] == "GB12345"


def test_get_foreign_apps_empty_for_missing(tmp_path):
    conn = _mem_db()
    conn.execute("INSERT INTO case_file VALUES ('71000001','1920-01-01')")
    _write_csv(tmp_path / "foreign_application.csv", [
        {"serial_no": "71000001", "foreign_appl_no": "GB12345",
         "foreign_country_cd": "GB", "foreign_filing_dt": "1919-06-01",
         "foreign_reg_no": None, "foreign_reg_dt": None},
    ])
    load_foreign_app(tmp_path, conn)
    assert get_foreign_apps(conn, "00000000") == []


def test_get_foreign_apps_empty_table():
    conn = _mem_db()
    assert get_foreign_apps(conn, "71000001") == []
