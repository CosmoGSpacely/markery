"""Tests for Phase 6D: trademark/fetch.py and trademark/queries.py get_extended_mark."""

from __future__ import annotations

from datetime import date

import duckdb
import pytest

from markery.specialist.trademark.fetch import fetch_mark_record, _upsert_extended_mark
from markery.specialist.trademark.queries import get_extended_mark

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXTENDED_DDL = """
CREATE TABLE IF NOT EXISTS extended_marks (
    serial_no         VARCHAR PRIMARY KEY,
    mark_text         VARCHAR,
    filing_dt         DATE,
    registration_no   VARCHAR,
    registration_dt   DATE,
    status_cd         VARCHAR,
    goods_desc        VARCHAR,
    intl_class        VARCHAR,
    owner_name        VARCHAR,
    first_use_dt      VARCHAR,
    first_use_comm_dt VARCHAR,
    raw_json          VARCHAR,
    fetched_dt        DATE
);
"""


def _mem_db() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:")
    conn.execute(_EXTENDED_DDL)
    return conn


def _parsed_record(**kwargs) -> dict:
    base = {
        "serial_no":          "71403472",
        "mark_text":          "SMEAD'S TELL VISION SYSTEM",
        "filing_dt":          "1938-02-26",
        "registration_no":    None,
        "registration_dt":    None,
        "status_cd":          "710",
        "goods_desc":         "Visible record systems.",
        "intl_class":         "016",
        "owner_name":         "Smead Manufacturing Company",
        "first_use_dt":       "1937-01-01",
        "first_use_comm_dt":  "1937-01-01",
        "raw_json":           '{"test": true}',
    }
    base.update(kwargs)
    return base


class _MockClient:
    def __init__(self, response=None):
        self._response = response

    def fetch_case_status(self, serial_no: str):
        if self._response is None:
            return None
        rec = dict(self._response)
        rec["serial_no"] = serial_no
        return rec


# ---------------------------------------------------------------------------
# _upsert_extended_mark
# ---------------------------------------------------------------------------

def test_upsert_inserts_new_record():
    conn = _mem_db()
    _upsert_extended_mark(conn, _parsed_record())
    row = conn.execute("SELECT serial_no, mark_text FROM extended_marks").fetchone()
    assert row[0] == "71403472"
    assert row[1] == "SMEAD'S TELL VISION SYSTEM"


def test_upsert_updates_existing_record():
    conn = _mem_db()
    _upsert_extended_mark(conn, _parsed_record(status_cd="710"))
    _upsert_extended_mark(conn, _parsed_record(status_cd="800"))
    n   = conn.execute("SELECT count(*) FROM extended_marks").fetchone()[0]
    row = conn.execute("SELECT status_cd FROM extended_marks WHERE serial_no = '71403472'").fetchone()
    assert n == 1
    assert row[0] == "800"


def test_upsert_sets_fetched_dt_today():
    conn = _mem_db()
    _upsert_extended_mark(conn, _parsed_record())
    row = conn.execute("SELECT fetched_dt FROM extended_marks").fetchone()
    assert row[0] == date.today()


# ---------------------------------------------------------------------------
# fetch_mark_record
# ---------------------------------------------------------------------------

def test_fetch_mark_record_returns_false_when_not_found():
    conn   = _mem_db()
    client = _MockClient(response=None)
    result = fetch_mark_record("71403472", client, conn)
    assert result is False
    assert conn.execute("SELECT count(*) FROM extended_marks").fetchone()[0] == 0


def test_fetch_mark_record_upserts_and_returns_true():
    conn   = _mem_db()
    client = _MockClient(response=_parsed_record())
    result = fetch_mark_record("71403472", client, conn)
    assert result is True
    row = conn.execute("SELECT serial_no FROM extended_marks").fetchone()
    assert row[0] == "71403472"


def test_fetch_mark_record_skips_existing_without_force():
    conn   = _mem_db()
    _upsert_extended_mark(conn, _parsed_record(status_cd="710"))

    call_count = [0]
    class _CountingClient:
        def fetch_case_status(self, _):
            call_count[0] += 1
            return _parsed_record(status_cd="800")

    result = fetch_mark_record("71403472", _CountingClient(), conn, force=False)
    assert result is False
    assert call_count[0] == 0
    # Original value unchanged
    row = conn.execute("SELECT status_cd FROM extended_marks").fetchone()
    assert row[0] == "710"


def test_fetch_mark_record_re_fetches_with_force():
    conn   = _mem_db()
    _upsert_extended_mark(conn, _parsed_record(status_cd="710"))
    client = _MockClient(response=_parsed_record(status_cd="800"))
    result = fetch_mark_record("71403472", client, conn, force=True)
    assert result is True
    row = conn.execute("SELECT status_cd FROM extended_marks").fetchone()
    assert row[0] == "800"


# ---------------------------------------------------------------------------
# get_extended_mark (trademark/queries.py)
# ---------------------------------------------------------------------------

def test_get_extended_mark_returns_record():
    conn = _mem_db()
    _upsert_extended_mark(conn, _parsed_record())
    result = get_extended_mark(conn, "71403472")
    assert result is not None
    assert result["serial_no"] == "71403472"
    assert result["mark_text"] == "SMEAD'S TELL VISION SYSTEM"
    assert result["owner_name"] == "Smead Manufacturing Company"


def test_get_extended_mark_returns_none_for_missing():
    conn = _mem_db()
    assert get_extended_mark(conn, "00000000") is None


def test_get_extended_mark_all_fields_present():
    conn = _mem_db()
    _upsert_extended_mark(conn, _parsed_record())
    result = get_extended_mark(conn, "71403472")
    for field in ["serial_no", "mark_text", "filing_dt", "registration_no",
                  "registration_dt", "status_cd", "goods_desc", "intl_class",
                  "owner_name", "first_use_dt", "first_use_comm_dt", "fetched_dt"]:
        assert field in result, f"Missing field: {field}"
