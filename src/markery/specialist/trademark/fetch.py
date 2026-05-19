"""Single-trademark fetch operations for trademarks.duckdb.

Fetches marks that are not in the bulk 1900-1939 CSV dataset — post-1939
filings or any serial number absent from case_file — into the extended_marks
table.  Distinct from enrich.py, which enriches bulk-dataset marks already
present in case_file with TSDR image and status data.

All DB connections are accepted as arguments so callers control lifetime
and tests can pass in-memory connections.
"""

from __future__ import annotations

from datetime import date

import duckdb

from markery.specialist.trademark.tsdr_client import TSDRClient


def fetch_mark_record(
    serial_no: str,
    client: TSDRClient,
    conn: duckdb.DuckDBPyConnection,
    force: bool = False,
) -> bool:
    """Fetch mark from TSDR and upsert into extended_marks.

    Returns True if stored, False if TSDR returned 404.
    When force=False, skips the API call if the record already exists.
    """
    if not force:
        if conn.execute(
            "SELECT 1 FROM extended_marks WHERE serial_no = ?", [serial_no]
        ).fetchone():
            return False

    parsed = client.fetch_case_status(serial_no)
    if not parsed:
        return False

    _upsert_extended_mark(conn, parsed)
    return True


def _upsert_extended_mark(
    conn: duckdb.DuckDBPyConnection,
    record: dict,
) -> None:
    """Insert or overwrite one row in extended_marks."""
    sno      = record["serial_no"]
    existing = conn.execute(
        "SELECT 1 FROM extended_marks WHERE serial_no = ?", [sno]
    ).fetchone()
    today = date.today()

    if existing:
        conn.execute(
            """UPDATE extended_marks
               SET mark_text=?, filing_dt=?, registration_no=?, registration_dt=?,
                   status_cd=?, goods_desc=?, intl_class=?, owner_name=?,
                   first_use_dt=?, first_use_comm_dt=?, raw_json=?, fetched_dt=?
               WHERE serial_no=?""",
            [
                record.get("mark_text"),        record.get("filing_dt"),
                record.get("registration_no"),  record.get("registration_dt"),
                record.get("status_cd"),        record.get("goods_desc"),
                record.get("intl_class"),       record.get("owner_name"),
                record.get("first_use_dt"),     record.get("first_use_comm_dt"),
                record.get("raw_json"),         today, sno,
            ],
        )
    else:
        conn.execute(
            """INSERT INTO extended_marks
               (serial_no, mark_text, filing_dt, registration_no, registration_dt,
                status_cd, goods_desc, intl_class, owner_name,
                first_use_dt, first_use_comm_dt, raw_json, fetched_dt)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                sno,
                record.get("mark_text"),        record.get("filing_dt"),
                record.get("registration_no"),  record.get("registration_dt"),
                record.get("status_cd"),        record.get("goods_desc"),
                record.get("intl_class"),       record.get("owner_name"),
                record.get("first_use_dt"),     record.get("first_use_comm_dt"),
                record.get("raw_json"),         today,
            ],
        )
    conn.commit()
