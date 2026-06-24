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
    """True if a mark image file is referenced in mark_images for this serial."""
    row = conn.execute(
        "SELECT 1 FROM mark_images "
        "WHERE serial_no = ? AND file IS NOT NULL LIMIT 1",
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


def search_by_design_code(
    conn: duckdb.DuckDBPyConnection,
    code_prefix: str,
    filing_before: str | None = None,
    goods_contains: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Return marks matching a design code prefix.

    code_prefix: e.g. "03" matches all animal marks (030101, 031701, …).
      Trailing dots are stripped so "03." works identically to "03".
    filing_before: restrict to filing_dt < YEAR-01-01.
    goods_contains: case-insensitive substring match on GS-type statement_text.

    Returns a list of dicts with keys:
      serial_no, mark_text, own_name, filing_dt, goods_desc (first 100 chars).
    Rows are ordered by filing_dt. Deduplicates on serial_no.
    """
    prefix = code_prefix.rstrip(".") + "%"
    wheres = ["ds.design_search_cd LIKE ?"]
    params: list = [prefix]

    if filing_before:
        wheres.append("cf.filing_dt < ?")
        params.append(f"{filing_before}-01-01")
    if goods_contains:
        wheres.append("LOWER(fg.statement_text) LIKE ?")
        params.append(f"%{goods_contains.lower()}%")

    where_clause = " AND ".join(wheres)
    params.append(limit)

    sql = f"""
        WITH first_owner AS (
            SELECT serial_no, own_name,
                   ROW_NUMBER() OVER (PARTITION BY serial_no ORDER BY own_seq) AS rn
            FROM owner
        ),
        first_goods AS (
            SELECT serial_no, statement_text,
                   ROW_NUMBER() OVER (PARTITION BY serial_no) AS rn
            FROM statement
            WHERE statement_type_cd LIKE 'GS%'
        )
        SELECT DISTINCT
            ds.serial_no,
            COALESCE(cf.mark_id_char, '(figurative)') AS mark_text,
            fo.own_name,
            cf.filing_dt,
            LEFT(fg.statement_text, 100) AS goods_desc
        FROM design_search ds
        JOIN case_file cf ON ds.serial_no = cf.serial_no
        LEFT JOIN first_owner fo ON ds.serial_no = fo.serial_no AND fo.rn = 1
        LEFT JOIN first_goods fg ON ds.serial_no = fg.serial_no AND fg.rn = 1
        WHERE {where_clause}
        ORDER BY cf.filing_dt
        LIMIT ?
    """
    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "serial_no": r[0],
            "mark_text": r[1],
            "own_name":  r[2],
            "filing_dt": str(r[3]) if r[3] else None,
            "goods_desc": r[4],
        }
        for r in rows
    ]


def mark_status_report(
    conn: duckdb.DuckDBPyConnection,
    tm_variants: list[str],
    dead_only: bool = False,
    pd_only: bool = False,
    pd_threshold_year: int | None = None,
) -> list[dict]:
    """Return live/dead/public-domain status for all serials matching tm_variants.

    tm_variants: owner names from variants.csv (trademark_owner / trademark_search sources).
    Returns a list of dicts: serial_no, mark_text, filing_dt, status_cd, live_dead, public_domain.
    Applies dead_only / pd_only filters when set.
    pd_threshold_year defaults to current year - 95.
    """
    from datetime import date as _date
    if not tm_variants:
        return []
    if pd_threshold_year is None:
        pd_threshold_year = _date.today().year - 95

    placeholders = ",".join("?" * len(tm_variants))
    rows = conn.execute(
        f"SELECT DISTINCT cf.serial_no, cf.mark_id_char, cf.filing_dt, cf.cfh_status_cd "
        f"FROM owner o JOIN case_file cf ON o.serial_no = cf.serial_no "
        f"WHERE o.own_name IN ({placeholders}) "
        f"ORDER BY cf.filing_dt",
        tm_variants,
    ).fetchall()

    def _is_dead(status_cd) -> bool:
        try:
            return int(status_cd) >= 700
        except (TypeError, ValueError):
            return False

    def _is_pd(filing_dt) -> bool:
        if filing_dt is None:
            return False
        year = filing_dt.year if hasattr(filing_dt, "year") else int(str(filing_dt)[:4])
        return year <= pd_threshold_year

    results = []
    for serial_no, mark_id_char, filing_dt, cfh_status_cd in rows:
        dead   = _is_dead(cfh_status_cd)
        pd_flag = _is_pd(filing_dt)
        if dead_only and not dead:
            continue
        if pd_only and not pd_flag:
            continue
        results.append({
            "serial_no":     serial_no,
            "mark_text":     mark_id_char or "(figurative)",
            "filing_dt":     str(filing_dt)[:10] if filing_dt else None,
            "status_cd":     cfh_status_cd,
            "live_dead":     "dead" if dead else "live",
            "public_domain": pd_flag,
        })
    return results


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
