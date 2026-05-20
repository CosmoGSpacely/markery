"""Pure read queries for trademarks.duckdb.

All functions accept an open DuckDB connection as their first argument so
callers control connection lifetime and tests can pass in-memory connections.
Use connect() to obtain a connection from the configured database path.
"""

from __future__ import annotations

import duckdb

from markery.common.config import DB

# serial_no is BIGINT in bulk tables (as delivered by the USPTO CSV source)
# and VARCHAR in extended_marks and mark_images (as returned by the TSDR API).
# Queries joining across the two must cast: CAST(cf.serial_no AS VARCHAR).


def connect() -> duckdb.DuckDBPyConnection:
    """Open a read-only connection to trademarks.duckdb."""
    return duckdb.connect(str(DB["trademarks"]), read_only=True)


def get_mark(conn: duckdb.DuckDBPyConnection, serial_no: str) -> dict | None:
    """Return a single trademark record from case_file, or None if not found."""
    row = conn.execute(
        "SELECT serial_no, mark_id_char, filing_dt, mark_draw_cd, "
        "       registration_no, cfh_status_cd "
        "FROM case_file WHERE serial_no = ?",
        [serial_no],
    ).fetchone()
    if not row:
        return None
    return {
        "serial_no":       str(row[0]),
        "mark_name":       row[1],
        "filing_dt":       row[2],
        "draw_cd":         row[3],
        "registration_no": row[4],
        "status_cd":       row[5],
    }


def has_image(conn: duckdb.DuckDBPyConnection, serial_no: str) -> bool:
    """True if a mark image blob exists in mark_images for this serial."""
    row = conn.execute(
        "SELECT 1 FROM mark_images "
        "WHERE serial_no = ? AND image_data IS NOT NULL LIMIT 1",
        [serial_no],
    ).fetchone()
    return row is not None


def has_case_status(conn: duckdb.DuckDBPyConnection, serial_no: str) -> bool:
    """True if a TSDR case status record exists in extended_marks for this serial."""
    row = conn.execute(
        "SELECT 1 FROM extended_marks WHERE serial_no = ? LIMIT 1",
        [serial_no],
    ).fetchone()
    return row is not None


def get_goods_desc(conn: duckdb.DuckDBPyConnection, serial_no: str) -> str | None:
    """Return goods/services text, checking statement table first then extended_marks."""
    row = conn.execute(
        "SELECT statement_text FROM statement WHERE serial_no = ? LIMIT 1",
        [serial_no],
    ).fetchone()
    if row and row[0]:
        return row[0]
    row = conn.execute(
        "SELECT goods_desc FROM extended_marks WHERE serial_no = ? LIMIT 1",
        [serial_no],
    ).fetchone()
    return row[0] if row else None


def get_extended_mark(conn: duckdb.DuckDBPyConnection, serial_no: str) -> dict | None:
    """Return one extended_marks record, or None if not found."""
    row = conn.execute(
        "SELECT serial_no, mark_text, filing_dt, registration_no, "
        "       registration_dt, status_cd, goods_desc, intl_class, "
        "       owner_name, first_use_dt, first_use_comm_dt, fetched_dt "
        "FROM extended_marks WHERE serial_no = ?",
        [serial_no],
    ).fetchone()
    if not row:
        return None
    return {
        "serial_no":          str(row[0]),
        "mark_text":          row[1],
        "filing_dt":          row[2],
        "registration_no":    row[3],
        "registration_dt":    row[4],
        "status_cd":          row[5],
        "goods_desc":         row[6],
        "intl_class":         row[7],
        "owner_name":         row[8],
        "first_use_dt":       row[9],
        "first_use_comm_dt":  row[10],
        "fetched_dt":         row[11],
    }


def get_events(
    conn: duckdb.DuckDBPyConnection,
    serial_no: str,
) -> list[dict]:
    """Return all events for a serial number, ordered by event_dt.

    Returns [] if the events table has not been loaded (via load_events()).
    """
    try:
        rows = conn.execute(
            "SELECT serial_no, event_dt, event_cd, event_desc_t, party_cd "
            "FROM events WHERE serial_no = ? ORDER BY event_dt",
            [serial_no],
        ).fetchall()
    except Exception:
        return []
    return [
        {
            "serial_no":    str(r[0]),
            "event_dt":     r[1],
            "event_cd":     r[2],
            "event_desc_t": r[3],
            "party_cd":     r[4],
        }
        for r in rows
    ]


def get_foreign_apps(
    conn: duckdb.DuckDBPyConnection,
    serial_no: str,
) -> list[dict]:
    """Return all foreign application records for a serial number.

    Returns [] if the foreign_app table has not been loaded (via load_foreign_app()).
    """
    try:
        rows = conn.execute(
            "SELECT serial_no, foreign_appl_no, foreign_country_cd, "
            "       foreign_filing_dt, foreign_reg_no, foreign_reg_dt "
            "FROM foreign_app WHERE serial_no = ? ORDER BY foreign_filing_dt",
            [serial_no],
        ).fetchall()
    except Exception:
        return []
    return [
        {
            "serial_no":          str(r[0]),
            "foreign_appl_no":    r[1],
            "foreign_country_cd": r[2],
            "foreign_filing_dt":  r[3],
            "foreign_reg_no":     r[4],
            "foreign_reg_dt":     r[5],
        }
        for r in rows
    ]


def get_missing_enrichment(
    conn: duckdb.DuckDBPyConnection,
    serial_nos: list[str],
) -> list[str]:
    """Return serial numbers that have no goods/services text in any source.

    Used by the prepare command and the Phase 6C resolution loop to identify
    which trademarks need TSDR enrichment before scoring or essay writing.
    """
    if not serial_nos:
        return []
    placeholders = ",".join("?" * len(serial_nos))
    with_stmt = {r[0] for r in conn.execute(
        f"SELECT serial_no FROM statement "
        f"WHERE serial_no IN ({placeholders}) "
        f"AND statement_text IS NOT NULL AND statement_text != ''",
        serial_nos,
    ).fetchall()}
    with_em = {r[0] for r in conn.execute(
        f"SELECT serial_no FROM extended_marks "
        f"WHERE serial_no IN ({placeholders}) "
        f"AND goods_desc IS NOT NULL AND goods_desc != ''",
        serial_nos,
    ).fetchall()}
    covered = with_stmt | with_em
    return [sn for sn in serial_nos if sn not in covered]
